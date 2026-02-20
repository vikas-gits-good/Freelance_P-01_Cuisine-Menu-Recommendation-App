from itertools import chain
from typing import Any, Dict, List, Literal, Tuple

from Src.Config import (
    Area,
    Locality,
    MainCuisine,
    Menu,
    MongoDBConfig,
    RelationshipParams,
    Restaurant,
)
from Src.Constants import MDBIndexKey, NodeLabels, RelationshipLabels
from Src.Utils import LogException, log_etl, pull_from_mongodb


class Transformer:
    """Class to transform raw scraped json data into a form that can be used to create
    nodes and relationships in a Knowledge Graph DB.
    """

    def __init__(self):
        self.lctn_files: Dict[str, list[Dict[str, Any]]] = {
            "Country": [],
            "State": [],
            "City": [],
        }
        md_cnf = MongoDBConfig()
        coll_dict = {
            MDBIndexKey.UNIQUE_COUNTRY: md_cnf.swiggy.coll_uq_cr_ids,
            MDBIndexKey.UNIQUE_STATE: md_cnf.swiggy.coll_uq_st_ids,
            MDBIndexKey.UNIQUE_CITY: md_cnf.swiggy.coll_uq_ct_ids,
        }

        for lctn, (idx_key, coll) in zip(self.lctn_files.keys(), coll_dict.items()):
            try:
                _data = pull_from_mongodb(
                    database=md_cnf.swiggy.database,
                    collection=coll,
                    idx_key=idx_key,
                    prefix="Loader",
                )
                if idx_key.value == "uniq_city":
                    self.city_data = _data

                for val in _data.values():
                    self.lctn_files[lctn].append(val)

            except Exception as e:
                LogException(e, logger=log_etl)
                continue

    def get_data(
        self,
        purpose: Literal["create", "upsert"] = "create",
        data_list: List[Dict[str, Any]] = [{}],
    ) -> Tuple[Dict[NodeLabels, List[Any]], Dict[RelationshipLabels, List[Any]]]:
        """Method to get transformed data for node and link creation.

        Args:
            purpose (Literal["create", "upsert"]):
                * Select `create` to get data to create a new `Graph` from scratch.
                * Select `upsert` to get data to upsert data into existing `Graph`.
                * Defaults to `"create"`.
            data_list (List[Dict[str, Any]], optional): Scraped .json data for upsert operation.

        Returns:
            (node_data, link_data) (Tuple[Dict[NodeLabels, List[Any]], Dict[RelationshipLabels, List[Any]]]):
                Flattened data for node and link creation. No nested dicts.
        """
        if purpose == "create":
            node_data, rstn_data = self._get_data_create()

        elif purpose == "upsert":
            node_data, rstn_data = self._get_data_upsert(data_list)

        else:
            node_data, rstn_data = {}, {}

        return node_data, rstn_data

    def _get_data_create(
        self,
    ) -> Tuple[Dict[NodeLabels, List[Any]], Dict[RelationshipLabels, List[Any]]]:
        node_data = {}
        rlsp_data = {}
        try:
            log_etl.info("Loader: Appending node data")
            node_data = {
                NodeLabels.COUNTRY: [],
                NodeLabels.STATE: [],
                NodeLabels.CITY: [],
            }
            for key, val in self.lctn_files.items():
                node_data[NodeLabels(key)] = val

            log_etl.info("Load: Appending relationship data")
            srch_data = {
                "country_lookup": {
                    item["params"]["name"]: {"ids": item["ids"]}
                    for item in node_data[NodeLabels.COUNTRY]
                },
                "state_lookup": {
                    item["params"]["name"]: {"ids": item["ids"]}
                    for item in node_data[NodeLabels.STATE]
                },
            }

            # MERGE (:Country {ids: ''})-[:HAS_STATE]->(:State {ids: ''})
            stte_dict_rlsp = [
                RelationshipParams.from_data(
                    srch_data, RelationshipLabels.HAS_STATE, item
                )
                for item in node_data[NodeLabels.STATE]
            ]
            rlsp_data[RelationshipLabels.HAS_STATE] = stte_dict_rlsp

            # MERGE (:State {ids: ''})-[:HAS_CITY]->(:City {ids: ''})
            city_dict_rlsp = [
                RelationshipParams.from_data(
                    srch_data, RelationshipLabels.HAS_CITY, item
                )
                for item in node_data[NodeLabels.CITY]
            ]
            rlsp_data[RelationshipLabels.HAS_CITY] = city_dict_rlsp

            del srch_data
            # for item in chain.from_iterable(
            #     chain(rlsp_data.values(), node_data.values())
            # ):
            #     # the '-' in 'ISO3166-2-lvl4' is causing Cypher to fail
            #     # also, UNWIND is failing for nested data
            #     # dont remove this comment incase of rollback
            #     item.pop("address", None)

        except Exception as e:
            LogException(e, logger=log_etl)
            # raise CustomException(e)

        return node_data, rlsp_data

    def _get_data_upsert(
        self,
        data_list: List[Dict[str, Any]] = [{}],
    ) -> Tuple[Dict[NodeLabels, List[Any]], Dict[RelationshipLabels, List[Any]]]:
        node_data = {}
        rlsp_data = {}
        try:
            node_data = {
                NodeLabels.AREA: [],
                NodeLabels.LOCALITY: [],
                NodeLabels.RESTAURANT: [],
                NodeLabels.MENU: [],
                NodeLabels.MAINCUISINE: [],
                # NodeLabels.SUBCUISINE: [],
                # include in production
            }
            rlsp_data = {
                RelationshipLabels.HAS_AREA: [],
                RelationshipLabels.HAS_LOCALITY: [],
                RelationshipLabels.HAS_RESTAURANT: [],
                RelationshipLabels.HAS_MENU: [],
                RelationshipLabels.SERVES_MAIN_CUISINE: [],
                # RelationshipLabels.SERVES_SUB_CUISINE: [],
                # include in production
            }

            city_keys = {key: val["ids"] for key, val in self.city_data.items()}

            for json_data in data_list:
                try:
                    rstn = Restaurant(**json_data["data"])
                    menu = Menu(**json_data["data"])
                    city_id = city_keys.get(rstn.city_id, "")
                    loca = {
                        "city_id": city_id,
                        "rstn": rstn,
                    }
                    area = Area(**loca)
                    lclt = Locality(**loca)
                    macs = MainCuisine(cuis=rstn.cuisines)
                    # sucs = SubCuisine(cuis=rstn.cuisines)

                    area_dict_node = area.to_node_dict()
                    lclt_dict_node = lclt.to_node_dict()
                    rstn_dict_node = rstn.to_node_dict()
                    menu_dict_node = menu.to_node_dict()
                    mcui_dict_node = macs.to_node_dict()
                    # scui_dict_node = sucs.to_node_dict()

                    node_data[NodeLabels.AREA].append(area_dict_node)
                    node_data[NodeLabels.LOCALITY].append(lclt_dict_node)
                    node_data[NodeLabels.RESTAURANT].append(rstn_dict_node)
                    node_data[NodeLabels.MENU].append(menu_dict_node)
                    node_data[NodeLabels.MAINCUISINE].append(mcui_dict_node)
                    # node_data[NodeLabels.SUBCUISINE].append(scui_dict_node)

                    rl_data = {
                        "city_id": city_id,
                        "rstn": rstn,
                        "menu": menu,
                        "area_dict_node": area_dict_node,
                        "lclt_dict_node": lclt_dict_node,
                    }

                    area_dict_rlsp = RelationshipParams.from_data(
                        rl_data, RelationshipLabels.HAS_AREA
                    )
                    lclt_dict_rlsp = RelationshipParams.from_data(
                        rl_data, RelationshipLabels.HAS_LOCALITY
                    )
                    rstn_dict_rlsp = RelationshipParams.from_data(
                        rl_data, RelationshipLabels.HAS_RESTAURANT
                    )
                    menu_dict_rlsp = [
                        RelationshipParams.from_data(
                            rl_data, RelationshipLabels.HAS_MENU, food
                        )
                        for food in menu.food_items
                    ]
                    mcui_dict_rlsp = [
                        RelationshipParams.from_data(
                            rl_data, RelationshipLabels.SERVES_MAIN_CUISINE, cuisine
                        )
                        for cuisine in rstn.cuisines
                    ]
                    # scui_dict_rlsp = [
                    #     RelationshipParams.from_data(
                    #         rl_data, RelationshipLabels.SERVES_SUB_CUISINE, cuisine
                    #     )
                    #     for cuisine in rstn.cuisines
                    # ]

                    # MERGE (:City {ids: ''})-[:HAS_AREA]->(:Area {ids: ''})
                    rlsp_data[RelationshipLabels.HAS_AREA].append(area_dict_rlsp)

                    # MERGE (:Area {ids: ''})-[:HAS_LOCALITY]->(:Locality {ids: ''})
                    rlsp_data[RelationshipLabels.HAS_LOCALITY].append(lclt_dict_rlsp)

                    # MERGE (:Locality {ids: ''})-[:HAS_RESTAURANT]->(:Restaurant {ids: ''})
                    rlsp_data[RelationshipLabels.HAS_RESTAURANT].append(rstn_dict_rlsp)

                    # MERGE (:Restaurant {ids: ''})-[:HAS_MENU]->(:Menu {name: ''})
                    rlsp_data[RelationshipLabels.HAS_MENU].append(menu_dict_rlsp)

                    # MERGE (:Restaurant {ids: ''})-[:SERVES_MAIN_CUISINE]->(:Cuisine {name: ''})
                    rlsp_data[RelationshipLabels.SERVES_MAIN_CUISINE].append(
                        mcui_dict_rlsp
                    )

                    ## MERGE (:Restaurant {ids: ''})-[:SERVES_SUB_CUISINE]->(:Cuisine {name: ''})
                    # rlsp_data[RelationshipLabels.SERVES_SUB_CUISINE].append(
                    #     scui_dict_rlsp
                    # )

                except Exception as e:
                    LogException(e, logger=log_etl)
                    log_etl.info(f"{rstn.ids = }")
                    continue

            del data_list  # clear memory

        except Exception as e:
            LogException(e, logger=log_etl)
            # raise CustomException(e)

        return node_data, rlsp_data
