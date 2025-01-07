import math, requests, asyncio, os
from dotenv import load_dotenv
load_dotenv()

async def individual_search(guild,args):
    url = f"https://discord.com/api/v9/guilds/{guild.id}/messages/search?{args}"

    print(f"Searching at {url}")

    while True:
        result = requests.get(url,headers={"authorization":os.getenv("TOKEN")})

        if result.status_code == 429:
            print(f"Ratelimited for {result.json()['retry_after']}, retrying")
            # Discord pretty consistently waits an extra bit
            await asyncio.sleep(float(result.json()["retry_after"])+0.01)
        elif result.status_code != 200:
            print(result)
            return result.json()
        else:
            return result.json()


async def get_all_results(guild,args):
    init_result = await individual_search(guild,args)
    messages = init_result["messages"]

    print(f"{init_result['total_results']} results, iterating {math.ceil(init_result['total_results']/25)} times")

    for i in range(math.ceil(init_result["total_results"]/25)-1):
        messages.extend((await individual_search(guild,f"{args}&offset={(i+1)*25}"))["messages"])

    return(messages)

def generate_search_arguments(content=None,author_id=None,channel_id=None,has=None,limit=25,mentions=None):
    args = ""
    if content:
        args += "content="+content+"&"
    if limit:
        args += "limit="+str(limit)+"&"
    if author_id:
        args += "author_id="+author_id+"&"
    if channel_id:
        args += "channel_id="+channel_id+"&"
    if has:
        args += "has="+has+"&"
    if mentions:
        args += "mentions="+has+"&"
    # print(args)
    return args

async def get_messages_count(guild,search_string,args=""):
    print(f"Getting message count for {search_string}")

    args += generate_search_arguments(content=search_string,limit=1)
    response = (await individual_search(guild,args))

    return int(response["total_results"])