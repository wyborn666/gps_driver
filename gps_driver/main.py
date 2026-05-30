import socket

from gps3 import gps3
import time
import os
import json
import utm

GPS_HOST = os.getenv("GPS_HOST", "gpsd")
GPS_PORT = int(os.getenv("GPS_PORT", 2947))
UDP_HOST = os.getenv("UDP_HOST", "127.0.0.1")
UDP_PORT = int(os.getenv("UDP_PORT", 5005))



def parse_tpv(data_stream):
    tpv = data_stream.TPV
    return {
        "time": tpv.get("time"),
        "lat": tpv.get("lat"),
        "lon": tpv.get("lon"),
        "alt": tpv.get("alt"),
        "speed": tpv.get("speed"),
        "track": tpv.get("track"),
    }


def to_utm(lat, lon):
    try:
        lat_f = float(lat)
        lon_f = float(lon)
    except (TypeError, ValueError):
        return None
    easting, northing, zone_number, zone_letter = utm.from_latlon(lat, lon)
    return {
        "easting": round(easting, 3),
        "northing": round(northing, 3),
        "zone_number": zone_number,
        "zone_letter": zone_letter
    }


def build_payload(raw):
    utm_coords = to_utm(raw["lat"], raw["lot"])
    return {
        "time":  raw["time"],
        "lat":   raw["lat"],
        "lon":   raw["lon"],
        "alt":   raw["alt"],
        "speed": raw["speed"],
        "track": raw["track"],
        "utm":   utm_coords,   # None, если координаты ещё не пришли
    }

udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

gps_socket = gps3.GPSDSocket()
data_stream = gps3.DataStream()

gps_socket.connect(host=GPS_HOST, port=GPS_PORT)
gps_socket.watch()


for new_data in gps_socket:
    if True:
        try:
            data_stream.unpack(new_data)
            raw = parse_tpv(data_stream)
        except Exception as e:
            print(f"[WARN] Ошибка разбора данных: {e}")
            time.sleep(0.5)
            continue

        payload = build_payload(raw)
        message = json.dumps(payload, ensure_ascii=False)

        try:
            udp_sock.sendto(message.encode("utf-8"), (UDP_HOST, UDP_PORT))
        except Exception as E:
            print(f"[WARN] Ошибка отправки UDP: {e}")
        print(message)
        time.sleep(0.5)