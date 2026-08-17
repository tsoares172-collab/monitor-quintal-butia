import hashlib
import os
import re
import requests
from bs4 import BeautifulSoup

URL = "https://quintalbutia.com.br/categoria/agenda/"
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
HASH_FILE = "last_hash.txt"


def send_telegram_message(message):
  if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
    print("Tokens do Telegram não foram configurados nas Secrets.")
    return

  api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
  payload = {
      "chat_id": TELEGRAM_CHAT_ID,
      "text": message,
      "parse_mode": "HTML",
      "disable_web_page_preview": False,
  }
  try:
    res = requests.post(api_url, json=payload, timeout=10)
    res.raise_for_status()
    print("Notificação enviada com sucesso ao Telegram!")
  except Exception as e:
    print(f"Erro ao enviar mensagem ao Telegram: {e}")


def check_website():
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
          " like Gecko) Chrome/120.0.0.0 Safari/537.36"
      )
  }

  try:
    response = requests.get(URL, headers=headers, timeout=15)
    response.raise_for_status()
  except Exception as e:
    print(f"Erro ao carregar a página: {e}")
    return

  soup = BeautifulSoup(response.text, "html.parser")

  # Foca especificamente na lista de produtos/eventos da agenda
  content_area = (
      soup.find("ul", class_="products")
      or soup.find("main")
      or soup.find("body")
  )
  text_content = (
      content_area.get_text(separator=" ", strip=True) if content_area else ""
  )

  # Remove espaços repetidos para evitar falsos alarmes por simples mudanças de layout
  clean_text = re.sub(r"\s+", " ", text_content)
  current_hash = hashlib.md5(clean_text.encode("utf-8")).hexdigest()

  previous_hash = ""
  if os.path.exists(HASH_FILE):
    with open(HASH_FILE, "r") as f:
      previous_hash = f.read().strip()

  if current_hash != previous_hash:
    print("Mudança na agenda detectada!")

    # Salva o novo estado
    with open(HASH_FILE, "w") as f:
      f.write(current_hash)

    # Dispara alerta apenas se não for a primeiríssima execução
    if previous_hash != "":
      msg = (
          "🚨 <b>NOVA ATUALIZAÇÃO NA AGENDA DO QUINTAL BUTIÁ!</b> 🚨\n\n"
          "Uma nova festa, ingresso ou alteração foi publicada no site.\n\n"
          f"🔗 <a href='{URL}'>Clique aqui para abrir a agenda</a>"
      )
      send_telegram_message(msg)
    else:
      print("Primeira execução concluída! O estado atual da agenda foi salvo.")
  else:
    print("Nenhuma novidade na agenda no momento.")


if __name__ == "__main__":
  check_website()
