from datetime import datetime, timezone
from typing import List

from src.RAG.User.Config.cyphers import UserCypherConfig
from src.RAG.User.Config.pool import UserMemoryPool
from src.RAG.User.schemas import PreferenceData, InteractionData, UserContext

from src.Logging.logger import log_flk
from src.Exception.exception import LogException


class UserMemory:
    """Core read/write operations for the user memory graph on FalkorDB DB 10."""

    def __init__(self):
        self._ucc = UserCypherConfig()
        self._pool = UserMemoryPool(size=2)
        self._cyp_set = self._ucc.cp_code.set
        self._cyp_get = self._ucc.cp_code.get
        self._cyp_put = self._ucc.cp_code.put

    # --------------------------------------------------------------------- #
    # Read operations
    # --------------------------------------------------------------------- #
    def get_user_context(self, user_id: str) -> UserContext:
        """Retrieve user preferences and latest summary for prompt injection.

        Args:
            user_id: Unique user identifier.

        Returns:
            UserContext with formatted preferences and summary strings.
        """
        graph = self._pool.acquire()
        try:
            # get preferences with confidence >= 0.5
            pref_result = graph.query(
                self._cyp_get["get_user_preferences"],
                {"user_id": user_id, "min_confidence": 0.5},
            )

            # get latest summary
            summ_result = graph.query(
                self._cyp_get["get_latest_summary"],
                {"user_id": user_id},
            )

            # format preferences into readable string
            prefs_text = "No preferences recorded yet."
            if pref_result.result_set:
                lines = []
                for row in pref_result.result_set:
                    cat, val, conf = row[0], row[1], row[2]
                    lines.append(f"- {cat}: {val} (confidence: {conf})")
                prefs_text = "\n".join(lines)

            # format summary
            summ_text = "No conversation history available."
            if summ_result.result_set:
                summ_text = summ_result.result_set[0][0]

            return UserContext(
                preferences_text=prefs_text,
                summary_text=summ_text,
            )

        except Exception as e:
            LogException(e, logger=log_flk)
            return UserContext()

        finally:
            self._pool.release(graph)

    # --------------------------------------------------------------------- #
    # Write operations
    # --------------------------------------------------------------------- #
    def ensure_user(self, user_id: str) -> None:
        """Create user node if it does not exist.

        Args:
            user_id: Unique user identifier.
        """
        graph = self._pool.acquire()
        try:
            now = datetime.now(timezone.utc).isoformat()
            graph.query(
                self._cyp_set["create_user_node"],
                {
                    "user_id": user_id,
                    "params": {"created_at": now, "last_active": now},
                },
            )

        except Exception as e:
            LogException(e, logger=log_flk)

        finally:
            self._pool.release(graph)

    def save_preferences(
        self, user_id: str, preferences: List[PreferenceData]
    ) -> None:
        """Upsert preference nodes for a user.

        Args:
            user_id: Unique user identifier.
            preferences: List of extracted preferences.
        """
        if not preferences:
            return

        graph = self._pool.acquire()
        try:
            now = datetime.now(timezone.utc).isoformat()
            for pref in preferences:
                graph.query(
                    self._cyp_set["create_preference_node"],
                    {
                        "user_id": user_id,
                        "category": pref.category,
                        "value": pref.value,
                        "params": {
                            "confidence": pref.confidence,
                            "explicit": pref.explicit,
                            "updated_at": now,
                        },
                    },
                )

        except Exception as e:
            LogException(e, logger=log_flk)

        finally:
            self._pool.release(graph)

    def save_interaction(
        self,
        user_id: str,
        session_id: str,
        turn_number: int,
        data: InteractionData,
    ) -> None:
        """Log an interaction node under the session.

        Args:
            user_id: Unique user identifier.
            session_id: Current session UUID.
            turn_number: Turn counter within session.
            data: Interaction details.
        """
        graph = self._pool.acquire()
        try:
            now = datetime.now(timezone.utc).isoformat()

            # ensure session exists
            graph.query(
                self._cyp_set["create_session_node"],
                {
                    "user_id": user_id,
                    "session_id": session_id,
                    "params": {"started_at": now},
                },
            )

            # create interaction
            graph.query(
                self._cyp_set["create_interaction_node"],
                {
                    "session_id": session_id,
                    "turn_number": turn_number,
                    "params": {
                        "query": data.query,
                        "intent": data.intent,
                        "tool_used": data.tool_used or "none",
                        "result_brief": data.result_brief,
                        "timestamp": now,
                    },
                },
            )

        except Exception as e:
            LogException(e, logger=log_flk)

        finally:
            self._pool.release(graph)

    def save_summary(self, user_id: str, summary_text: str, version: int) -> None:
        """Create a new summary node for the user.

        Args:
            user_id: Unique user identifier.
            summary_text: Compressed conversation summary.
            version: Summary version number (increments over time).
        """
        graph = self._pool.acquire()
        try:
            now = datetime.now(timezone.utc).isoformat()
            graph.query(
                self._cyp_set["create_summary_node"],
                {
                    "user_id": user_id,
                    "params": {
                        "text": summary_text,
                        "version": version,
                        "created_at": now,
                    },
                },
            )

        except Exception as e:
            LogException(e, logger=log_flk)

        finally:
            self._pool.release(graph)

    def update_last_active(self, user_id: str) -> None:
        """Update the user's last_active timestamp."""
        graph = self._pool.acquire()
        try:
            now = datetime.now(timezone.utc).isoformat()
            graph.query(
                self._cyp_put["update_user_last_active"],
                {"user_id": user_id, "timestamp": now},
            )

        except Exception as e:
            LogException(e, logger=log_flk)

        finally:
            self._pool.release(graph)

    def cleanup(self, user_id: str, keep_interactions: int = 20, keep_summaries: int = 3) -> None:
        """Prune old interactions and summaries.

        Args:
            user_id: Unique user identifier.
            keep_interactions: Number of recent interactions to keep.
            keep_summaries: Number of recent summaries to keep.
        """
        graph = self._pool.acquire()
        try:
            graph.query(
                self._cyp_put["delete_old_interactions"],
                {"user_id": user_id, "keep_count": keep_interactions},
            )
            graph.query(
                self._cyp_put["delete_old_summaries"],
                {"user_id": user_id, "keep_count": keep_summaries},
            )

        except Exception as e:
            LogException(e, logger=log_flk)

        finally:
            self._pool.release(graph)

    # --------------------------------------------------------------------- #
    # Setup (run once)
    # --------------------------------------------------------------------- #
    def create_indexes(self) -> None:
        """Create indexes on user memory graph. Run once during setup."""
        graph = self._pool.acquire()
        try:
            index_queries = self._cyp_set.get("create_index", "")
            for line in index_queries.strip().split("\n"):
                line = line.strip()
                if line:
                    graph.query(line)
                    log_flk.info(f"UserMemory: Created index — {line}")

        except Exception as e:
            LogException(e, logger=log_flk)

        finally:
            self._pool.release(graph)
