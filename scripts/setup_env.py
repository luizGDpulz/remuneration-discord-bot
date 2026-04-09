from __future__ import annotations

from dataclasses import dataclass
from getpass import getpass
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT_DIR / ".env"


@dataclass(slots=True)
class EnvField:
    key: str
    prompt: str
    default: str = ""
    required: bool = False
    secret: bool = False


FIELDS = [
    EnvField(
        key="DISCORD_BOT_TOKEN",
        prompt="Token do bot do Discord",
        required=True,
        secret=True,
    ),
    EnvField(
        key="DISCORD_SYNC_GUILD_ID",
        prompt="ID do servidor de teste para sincronizacao rapida dos slash commands",
        default="",
    ),
    EnvField(
        key="DB_HOST",
        prompt="Host do MariaDB na rede Docker",
        default="mariadb",
        required=True,
    ),
    EnvField(
        key="DB_PORT",
        prompt="Porta do MariaDB",
        default="3306",
        required=True,
    ),
    EnvField(
        key="DB_NAME",
        prompt="Nome do banco usado pelo bot",
        default="discord_paid_breaks",
        required=True,
    ),
    EnvField(
        key="DB_USER",
        prompt="Usuario do banco para o bot",
        default="discord_bot",
        required=True,
    ),
    EnvField(
        key="DB_PASSWORD",
        prompt="Senha do usuario do banco",
        required=True,
        secret=True,
    ),
    EnvField(
        key="TZ",
        prompt="Timezone para exibicao dos horarios",
        default="America/Sao_Paulo",
        required=True,
    ),
    EnvField(
        key="LOG_LEVEL",
        prompt="Nivel de log",
        default="INFO",
        required=True,
    ),
    EnvField(
        key="DB_POOL_MIN_SIZE",
        prompt="Tamanho minimo do pool de conexoes",
        default="1",
        required=True,
    ),
    EnvField(
        key="DB_POOL_MAX_SIZE",
        prompt="Tamanho maximo do pool de conexoes",
        default="10",
        required=True,
    ),
    EnvField(
        key="DB_DOCKER_NETWORK",
        prompt="Nome da rede Docker externa do MariaDB",
        default="mariadb-net",
        required=True,
    ),
]


def load_existing_env(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def ask_value(field: EnvField, current_value: str) -> str:
    default_hint = current_value if current_value else field.default
    suffix = f" [{default_hint}]" if default_hint else ""

    while True:
        if field.secret:
            typed = getpass(f"{field.prompt}{suffix}: ")
        else:
            typed = input(f"{field.prompt}{suffix}: ").strip()

        if typed:
            return typed
        if current_value:
            return current_value
        if field.default:
            return field.default
        if not field.required:
            return ""
        print("Esse campo e obrigatorio.")


def mask_value(field: EnvField, value: str) -> str:
    if field.secret and value:
        return "***"
    return value or "(vazio)"


def build_env_content(values: dict[str, str]) -> str:
    lines = [
        f"DISCORD_BOT_TOKEN={values['DISCORD_BOT_TOKEN']}",
        f"DISCORD_SYNC_GUILD_ID={values['DISCORD_SYNC_GUILD_ID']}",
        "",
        f"DB_HOST={values['DB_HOST']}",
        f"DB_PORT={values['DB_PORT']}",
        f"DB_NAME={values['DB_NAME']}",
        f"DB_USER={values['DB_USER']}",
        f"DB_PASSWORD={values['DB_PASSWORD']}",
        "",
        f"TZ={values['TZ']}",
        f"LOG_LEVEL={values['LOG_LEVEL']}",
        f"DB_POOL_MIN_SIZE={values['DB_POOL_MIN_SIZE']}",
        f"DB_POOL_MAX_SIZE={values['DB_POOL_MAX_SIZE']}",
        "",
        "# Rede Docker externa onde o MariaDB existente ja esta conectado.",
        f"DB_DOCKER_NETWORK={values['DB_DOCKER_NETWORK']}",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    print("Assistente de configuracao do .env para o bot de cagada remunerada")
    print(f"Arquivo de destino: {ENV_FILE}")
    print("")

    existing = load_existing_env(ENV_FILE)
    answers: dict[str, str] = {}

    for field in FIELDS:
        current_value = existing.get(field.key, "")
        answers[field.key] = ask_value(field, current_value)

    print("")
    print("Resumo da configuracao:")
    for field in FIELDS:
        print(f"- {field.key} = {mask_value(field, answers[field.key])}")

    print("")
    confirm = input("Gravar essas configuracoes em .env? [s/N]: ").strip().lower()
    if confirm not in {"s", "sim", "y", "yes"}:
        print("Operacao cancelada. Nenhum arquivo foi alterado.")
        return

    ENV_FILE.write_text(build_env_content(answers), encoding="utf-8")
    print("")
    print(".env salvo com sucesso.")
    print("Proximos passos sugeridos:")
    print("1. Confira se o bot foi convidado ao servidor com applications.commands")
    print("2. Suba com: docker compose up -d --build")
    print("3. Veja os logs com: docker compose logs -f remuneration-bot")


if __name__ == "__main__":
    main()
