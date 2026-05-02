import json
import os
import click
import anthropic
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
    client = anthropic.Anthropic(api_key=cfg["llm"]["api_key"])

    user_prompt = USER_PROMPT_TEMPLATE.format(idea=idea, style=style)

    started_at = datetime.now(timezone.utc)

    message = client.messages.create(
        model=cfg["llm"]["model"],
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    finished_at = datetime.now(timezone.utc)
    duration = (finished_at - started_at).total_seconds()

    screenplay = json.loads(message.content[0].text)

    os.makedirs(os.path.dirname(output), exist_ok=True)
    with open(output, "w") as f:
        json.dump(screenplay, f, ensure_ascii=False, indent=2)

    write_manifest(
        os.path.dirname(output), 0, "screenplay",
        status="success",
        input={"idea": idea, "style": style},
        output={"screenplay": output},
        model={"provider": cfg["llm"]["provider"], "model": cfg["llm"]["model"]},
        timing={
            "started_at": started_at.isoformat(),
            "finished_at": finished_at.isoformat(),
            "duration_sec": duration,
        },
        error={"type": None, "message": None, "retry_count": 0, "recoverable": None, "occurred_at": None},
    )


if __name__ == "__main__":
    cli()
