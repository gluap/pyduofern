import time

from pyduofern.duofern_stick import DuofernStick

stick = DuofernStick()
stick._initialize()
stick.start()

time.sleep(12)
# print(stick.command("409882", "up"))

# print(duo.set("409882","position",100))

while True:
    for item in stick.config["devices"]:
        time.sleep(1)
        if "Küche" in item['name']:
            stick.command(item["id"], "position", 95)
            print(item)
            print(stick.duofern_parser.modules['by_code'][item['id']])
stick.stop()
stick.join()
