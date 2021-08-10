import asyncio
from time import time
from typing import *
from wizwalker.constants import Keycode
from wizwalker.extensions.wizsprinter import SprintyCombat, CombatConfigProvider, WizSprinter
from wizwalker.client import Client
from wizwalker.memory import DynamicClientObject
from utils import decide_heal


async def go_to_closest_mob(self, excluded_ids: Set[int] = None) -> bool:
        return await go_to_closest_of(self,await self.get_mobs(excluded_ids), False)

async def go_to_closest_of(self, entities: List[DynamicClientObject], only_safe: bool = False):
    if e := await self.find_closest_of_entities(entities, only_safe):
        ev = await e.location()
        await self.goto(ev.x, ev.y)
        return True
    return False

async def go_to_closest_health_wisp(self, only_safe: bool = False, excluded_ids: Set[int] = None) -> bool:
        return await go_to_closest_of(self,await self.get_health_wisps(excluded_ids), False)

async def go_to_closest_mana_wisp(self, only_safe: bool = False, excluded_ids: Set[int] = None) -> bool:
        return await go_to_closest_of(self,await self.get_mana_wisps(excluded_ids), False)

async def main(sprinter):
    # Register clients
    sprinter.get_new_clients()
    clients = sprinter.get_ordered_clients()
    p1, p2, p3, p4 = [*clients, None, None, None, None][:4]
    for i, p in enumerate(clients, 1):
        p.title = "p" + str(i)

    # Hook activation
    for p in clients: 
      print(f"[{p.title}] Activating Hooks")
      await p.activate_hooks()
      await p.mouse_handler.activate_mouseless()
      await p.send_key(Keycode.PAGE_DOWN, 0.1)
      
    print()
    Total_Count = 0
    total = time()
    while True:
        start = time()

        # Initial battle starter
        await go_to_closest_mob(p1)
        for p in clients[1:]:
            p1battle = await p1.body.position()
            await p.goto(p1battle.x,p1battle.y)
            await p.send_key(Keycode.W, 0.1)
            await asyncio.sleep(0.2)

        # Battle:
        combat_handlers = []
        print("Initiating combat")
        for p in clients: # Setting up the parsed configs to combat_handlers
            combat_handlers.append(SprintyCombat(p, CombatConfigProvider(f'cp/configs/{p.title}spellconfig.txt', cast_time=2,)))
        await asyncio.gather(*[h.wait_for_combat() for h in combat_handlers]) # .wait_for_combat() to wait for combat to then go through the battles
        print("Combat ended")

        # Unghosting
        await asyncio.sleep(0.4)
        await asyncio.gather(*[p.send_key(Keycode.S, .3) for p in clients])
        await asyncio.gather(*[p.send_key(Keycode.W, .3) for p in clients])
        
        # Healing
        for p in clients:
                total_health=await p.stats.max_hitpoints()
                if await p.stats.current_hitpoints() < 0.3 * total_health:
                        await go_to_closest_health_wisp(p)
        
        for p in clients:
                total_mana=await p.stats.max_mana()
                if await p.stats.current_mana() < 0.3 * total_mana:
                        await go_to_closest_mana_wisp(p)
                
        await asyncio.sleep(0.1)
        await asyncio.gather(*[p.use_potion_if_needed(health_percent=10, mana_percent=5) for p in clients]) # WizSprinter function now, not WizSDK
        await asyncio.gather(*[decide_heal(p) for p in clients])
        await asyncio.sleep(5)


        # Time
        Total_Count += 1
        print("The Total Amount of Runs: ", Total_Count)
        print("Time Taken for run: ", round((time() - start) / 60, 2), "minutes")
        print("Total time elapsed: ", round((time() - total) / 60, 2), "minutes")
        print("Average time per run: ", round(((time() - total) / 60) / Total_Count, 2), "minutes")


# Error Handling
async def run():
  sprinter = WizSprinter()

  try:
    await main(sprinter)
  except:
    import traceback

    traceback.print_exc()

  await sprinter.close()


# Start
if __name__ == "__main__":
    asyncio.run(run())
