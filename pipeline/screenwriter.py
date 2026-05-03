import json
import os
import click
import anthropic
import openai
from datetime import datetime, timezone
from pipeline.config import load_config
from pipeline.manifest import write_manifest


SYSTEM_PROMPT = """You are a professional screenwriter specializing in short films.

Generate a structured screenplay in JSON format based on the given idea and style.

Rules:
- Create 2-5 shots
- Each shot duration: 2-6 seconds
- Each character must have a detailed "appearance" description (Chinese)
- "character" can be null for establishing shots (no person)
- "dialogue" can be null for silent shots
- "emotion" can be null when character is null
- "motion" can be null
- "ambient" can be null

Return ONLY valid JSON. No markdown, no explanation."""


USER_PROMPT_TEMPLATE = """Idea: {idea}
Style: {style}

Generate the screenplay JSON following this exact structure:
{{
  "meta": {{
    "title": "string",
    "style": "{style}",
    "total_duration_est": number
  }},
  "characters": {{
    "name": {{
      "appearance": "detailed description in Chinese",
      "voice_id": "male_01" or "female_01"
    }}
  }},
  "shots": [
    {{
      "shot_id": 1,
      "character": "name or null",
      "dialogue": "text or null",
      "emotion": "emotion or null",
      "scene_desc": "visual description in Chinese",
      "camera": "shot type in Chinese",
      "motion": "movement or null",
      "ambient": "sound or null",
      "duration_sec": integer,
      "transition": "硬切"
    }}
  ]
}}"""


def _create_llm_client(cfg):
    provider = cfg.get("provider", "")
    api_base = cfg.get("api_base") or None
    if provider == "anthropic":
        return "anthropic", anthropic.Anthropic(
            api_key=cfg["api_key"],
            base_url=api_base,
        )
    else:
        return "openai", openai.OpenAI(
            api_key=cfg["api_key"],
            base_url=api_base,
        )


@click.group()
def cli():
    pass


@cli.command()
@click.option("--idea", required=True, help="Creative idea for the story")
@click.option("--style", required=True, help="Visual style description")
@click.option("--output", required=True, help="Path for screenplay JSON output")
@click.option("--config", default="config.yaml", help="Path to config file")
def generate(idea, style, output, config):
    cfg = load_config(config)
    llm_cfg = cfg["llm"]
    params = llm_cfg.get("params", {})
    max_tokens = params.get("max_tokens", 4096)

    provider_kind, client = _create_llm_client(llm_cfg)

    user_prompt = USER_PROMPT_TEMPLATE.format(idea=idea, style=style)

    started_at = datetime.now(timezone.utc)

    if provider_kind == "anthropic":
        message = client.messages.create(
            model=llm_cfg["model"],
            max_tokens=max_tokens,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        result_text = message.content[0].text
    else:
        message = client.chat.completions.create(
            model=llm_cfg["model"],
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
        result_text = message.choices[0].message.content

    finished_at = datetime.now(timezone.utc)
    duration = (finished_at - started_at).total_seconds()

    screenplay = json.loads(result_text)

    os.makedirs(os.path.dirname(output), exist_ok=True)
    with open(output, "w") as f:
        json.dump(screenplay, f, ensure_ascii=False, indent=2)

    write_manifest(
        os.path.dirname(output), 0, "screenplay",
        status="success",
        input={"idea": idea, "style": style},
        output={"screenplay": output},
        model={"provider": llm_cfg["provider"], "model": llm_cfg["model"]},
        timing={
            "started_at": started_at.isoformat(),
            "finished_at": finished_at.isoformat(),
            "duration_sec": duration,
        },
        error={"type": None, "message": None, "retry_count": 0, "recoverable": None, "occurred_at": None},
    )


if __name__ == "__main__":
    cli()
