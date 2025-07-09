from twilio.rest import Client
from typing import Any, Dict
from datetime import datetime, timezone
from dotenv import load_dotenv
import os
from urllib.request import urlopen
import json

load_dotenv()

twilio_token = os.getenv("TWILIO_TOKEN")
twilio_id = os.getenv("TWILIO_ID")

def get_upcoming_races(json_data : Dict[str, Any]) -> list[Dict[str, Any]]:
  races_upcoming = []

  for date_key, race in json_data.items():
            if not race[0]["completed"]:
              races_upcoming.append({
                "gPrx": race[0].get("gPrx", "Sin nombre"),
                "crct": race[0].get("crct", "Sin circuito"),
                "startDate": race[0].get("startDate"),
                "endDate": race[0].get("endDate")
              })

  return races_upcoming

def current_day() :
  now = datetime.now()
  date = now.date()
  return date

def max_speed(latest_race) -> str:

  session_key = latest_race["session_key"]

  lap_response = urlopen(f"https://api.openf1.org/v1/laps?session_key={session_key}")
  lap_data = json.loads(lap_response.read().decode("utf-8"))

  lap_data = [lap for lap in lap_data if isinstance(lap.get("st_speed"), (int, float))]

  if lap_data:
    fastest = max(lap_data, key=lambda x: x["st_speed"])
    speed = fastest["st_speed"]
    driver_number = fastest["driver_number"]

    driver_url = f"https://api.openf1.org/v1/drivers?driver_number={driver_number}&session_key={session_key}"
    driver_data = json.loads(urlopen(driver_url).read().decode("utf-8"))
    name = driver_data[0].get("full_name", f"N° {driver_number}") if driver_data else f"N° {driver_number}"

  return f'🚀Velocidad máxima: {name} arrasó en línea recta con  {speed} km/h, dominando el speed trap y dejando atrás a varios de la parrilla.'

def most_positions_gained(latest_race) -> str:
  meeting_key = latest_race["meeting_key"]

  try:
    qualy_url = f"https://api.openf1.org/v1/starting_grid?meeting_key={meeting_key}"
    qualy_data = json.loads(urlopen(qualy_url).read().decode("utf-8"))

    race_url = f"https://api.openf1.org/v1/session_result?meeting_key={meeting_key}"
    race_data = json.loads(urlopen(race_url).read().decode("utf-8"))

    qualy_pos = {}
    race_pos = {}

    for q in qualy_data:
      if isinstance(q.get("position"), int):
        qualy_pos[q["driver_number"]] = q["position"]

    for r in race_data:
      if isinstance(r.get("position"), int):
        race_pos[r["driver_number"]] = r["position"]

    deltas = {}
    for num in race_pos:
      if num in qualy_pos:
        start = qualy_pos[num]
        end = race_pos[num]
        gain = start - end
        if gain > 0:
          deltas[num] = {"delta": gain, "start": start, "end": end}

    best_num, best_data = max(deltas.items(), key=lambda x: x[1]["delta"])
    driver_url = f"https://api.openf1.org/v1/drivers?driver_number={best_num}&meeting_key={meeting_key}"
    driver_data = json.loads(urlopen(driver_url).read().decode("utf-8"))
    name = driver_data[0].get("full_name", f"N° {best_num}") if driver_data else f"N° {best_num}"

    return f"📈 Posiciones ganadas: {name} ganó {best_data['delta']} posiciones, largando en P{best_data['start']} y finalizando en P{best_data['end']}."

  except Exception as e:
    return f"❌ Error al calcular posiciones ganadas desde la qualy: {e}"

def format_lap_time(seconds: float) -> str:
  minutes = int(seconds // 60)
  secs = seconds % 60
  return f"{minutes}:{secs:06.3f}"

def latest_race():
  now = datetime.now()
  current_year = now.year

  try:
    response = urlopen(f'https://api.openf1.org/v1/sessions?year={current_year}&session_type=Race')
    sessions = json.loads(response.read().decode('utf-8'))
    sessions = [s for s in sessions if s.get("date_start")]
    print(sessions)

    for s in sessions:
      s["date_start_dt"] = datetime.fromisoformat(s["date_start"]).replace(tzinfo=None)

    past_sessions = [s for s in sessions if s["date_start_dt"] < now]
  except Exception as e:
    return f"Error al obtener o procesar sesiones: {e}"

  if not past_sessions:
    return "Aún no se ha disputado ninguna carrera este año."

  latest_race = max(past_sessions, key=lambda x: x["date_start_dt"])

  return latest_race

def fastest_lap(latest_race) -> str:

  session_key = latest_race["session_key"]

  lap_response = urlopen(f"https://api.openf1.org/v1/laps?session_key={session_key}")
  lap_data = json.loads(lap_response.read().decode("utf-8"))
  lap_time_data = [lap for lap in lap_data if isinstance(lap.get("lap_duration"), (int, float))]

  if lap_time_data:
    fastest_lap = min(lap_time_data, key=lambda x: x["lap_duration"])
    lap_time = fastest_lap["lap_duration"]
    driver_number = fastest_lap["driver_number"]

    driver_url = f"https://api.openf1.org/v1/drivers?driver_number={driver_number}&session_key={session_key}"
    driver_data = json.loads(urlopen(driver_url).read().decode("utf-8"))
    name = driver_data[0].get("full_name", f"N° {driver_number}") if driver_data else f"N° {driver_number}"
  return f'⏱️Vuelta más rápida: {name} marcó un tiempo imbatible de {format_lap_time(lap_time)} en la vuelta {fastest_lap['lap_number']}, aprovechando al máximo el momento óptimo de pista y neumáticos.'

def winners(last_race):
  session_key = last_race["session_key"]

  race_url = f"https://api.openf1.org/v1/session_result?session_key={session_key}"
  race_data = json.loads(urlopen(race_url).read().decode("utf-8"))

  podium_data = sorted(
    [pilot for pilot in race_data if pilot['position'] in [1, 2, 3]],
    key=lambda x: x['position']
  )

  podium = [pilot['driver_number'] for pilot in podium_data]

  names = []
  for driver in podium:
    url = f"https://api.openf1.org/v1/drivers?driver_number={driver}&session_key={session_key}"
    data = json.loads(urlopen(url).read().decode("utf-8"))

    if isinstance(data, list) and data:
      name = data[0].get("full_name", f"N° {driver}")
    else:
      name = f"N° {driver}"

    names.append(name)

  podium_message = f"""🏆 ¡Podio del Gran Premio!
                          🥇 1° lugar: {names[0]}
                          🥈 2° lugar: {names[1]}
                          🥉 3° lugar: {names[2]}"""

  return podium_message

def fast_pit(latest_race):

  session_key = latest_race["session_key"]

  pit_response = urlopen(f"https://api.openf1.org/v1/pit?session_key={session_key}")
  pit_data = json.loads(pit_response.read().decode("utf-8"))

  pit_data = [p for p in pit_data if isinstance(p.get("pit_duration"), (int, float))]

  if pit_data:
    shortest_pit = min(pit_data, key=lambda x: x["pit_duration"])
    pit_time = round(shortest_pit["pit_duration"], 3)
    driver_number = shortest_pit["driver_number"]
    lap_number = shortest_pit.get("lap_number", "¿desconocida?")

    driver_url = f"https://api.openf1.org/v1/drivers?driver_number={driver_number}&session_key={session_key}"
    driver_data = json.loads(urlopen(driver_url).read().decode("utf-8"))
    name = driver_data[0].get("full_name", f"N° {driver_number}") if driver_data else f"N° {driver_number}"

    return f'🛠️ Parada en boxes más corta: {name}  con una detención de solo {pit_time} segundos en la vuelta {lap_number}.'

def race_about() -> str:

    last_race = latest_race()

    race_info = is_race_week()

    if race_info != 0:
      country, circuit, fecha = race_info
      message = f"""📢 ¡Semana de Carrera!  El GP de {country} se corre en {circuit} esta semana ({fecha}).
      🏁 Repasemos cómo fue la última batalla sobre ruedas en el Gran Premio de {last_race['country_name']}, disputado el {last_race['date_end'].split('T')[0]} en el icónico circuito de {last_race['circuit_short_name']}, el cúal nos regaló un cierre vibrante con un podio digno de aplausos:
      {winners(last_race)}
      🗓️ Y como si eso fuera poco, estas joyitas estadísticas completaron una carrera inolvidable:
      {fastest_lap(last_race)}
      {max_speed(last_race)}
      {fast_pit(last_race)}
      {most_positions_gained(last_race)}
      """
      return message
    return f'No hay carrera esta semana😔'

def is_race_week(test_date=None, year=None):
    today = test_date or datetime.now(timezone.utc).date()
    year = year or today.year

    url = "https://api.openf1.org/v1/meetings"
    data = json.loads(urlopen(url).read().decode("utf-8"))

    for event in data:

        if event.get("year") != year:
            continue

        date_str = event.get("date_start")
        if not date_str:
            continue

        meeting_date = datetime.fromisoformat(date_str).date()

        if abs((meeting_date - today).days) <= 3:
            country = event.get("country_name", "País desconocido")
            circuit = event.get("circuit_short_name", "Circuito desconocido")
            fecha = meeting_date.strftime("%Y-%m-%d")
            return country, circuit, fecha
    return 0

def send_message():
  account_sid = twilio_id
  auth_token = twilio_token
  client = Client(account_sid, auth_token)

  message = client.messages.create(
    from_='whatsapp:+14155238886',
    body=f'{race_about()}',
    to='whatsapp:+5493815830731'

  )

send_message()
