class GroqModelList:
    class NCAI:
        allam_2_7b: str = "allam-2-7b"

    class Groq:
        compound: str = "groq/compound"
        compound_mini: str = "groq/compound-mini"

    class Meta:
        llama_31_8b_instant: str = "llama-3.1-8b-instant"
        llama_33_70b_versatile: str = "llama-3.3-70b-versatile"
        llama_4_maverick_17b_128e_instruct: str = (
            "meta-llama/llama-4-maverick-17b-128e-instruct"
        )
        llama_4_scout_17b_16e_instruct: str = (
            "meta-llama/llama-4-scout-17b-16e-instruct"
        )
        llama_guard_4_12b: str = "meta-llama/llama-guard-4-12b"
        llama_prompt_guard_2_22m: str = "meta-llama/llama-prompt-guard-2-22m"
        llama_prompt_guard_2_86m: str = "meta-llama/llama-prompt-guard-2-86m"

    class Qwen:
        qwen3_32b: str = "qwen/qwen3-32b"

    class Moonshot:
        kimi_k2_instruct: str = "moonshotai/kimi-k2-instruct"
        kimi_k2_instruct_0905: str = "moonshotai/kimi-k2-instruct-0905"

    class OpenAI:
        gpt_oss_20b: str = "openai/gpt-oss-20b"
        gpt_oss_safeguard_20b: str = "openai/gpt-oss-safeguard-20b"
        gpt_oss_120b: str = "openai/gpt-oss-120b"


class OpenAIModelList:
    class GPT_3:
        gpt_3_5_turbo: str = "gpt-3.5-turbo"
        gpt_3_5_turbo_16k: str = "gpt-3.5-turbo-16k"
        gpt_3_5_turbo_0613: str = "gpt-3.5-turbo-0613"
        gpt_3_5_turbo_1106: str = "gpt-3.5-turbo-1106"

    class GPT_4:
        gpt_4: str = "gpt-4"
        gpt_4_32k: str = "gpt-4-32k"
        gpt_4_0613: str = "gpt-4-0613"
        gpt_4_32k_0613: str = "gpt-4-32k-0613"
        gpt_4_turbo: str = "gpt-4-turbo"
        gpt_4o: str = "gpt-4o"
        gpt_4o_mini: str = "gpt-4o-mini-2024-07-18"
        gpt_4_1: str = "gpt-4.1"
        gpt_4_1_mini: str = "gpt-4.1-mini"
        gpt_4_1_nano: str = "gpt-4.1-nano"

    class GPT_5:
        gpt_5: str = "gpt-5"
        gpt_5_mini: str = "gpt-5-mini"
        gpt_5_nano: str = "gpt-5-nano"
        gpt_5_1: str = "gpt-5.1"
        gpt_5_2: str = "gpt-5.2"
        gpt_5_2_pro: str = "gpt-5.2-pro"
        gpt_5_2_codex: str = "gpt-5.2-codex"
