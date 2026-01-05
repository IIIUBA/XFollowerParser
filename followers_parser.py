import asyncio
import json
from curl_cffi.requests import AsyncSession

TARGET_USERNAME = "AxiomExchange"
LIMIT = 5000
OUTPUT_FILE = "followers_list.txt"
PROXY = "http://log:pass@ip:port"

COOKIES = {
    "auth_token": "",
    "ct0": ""
}

headers = {
    "authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA",
    "x-csrf-token": COOKIES["ct0"],
    "content-type": "application/json",
    "referer": "https://x.com/",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

async def get_user_id(session, username):
    url = "https://x.com/i/api/graphql/sLVLhk0bGj3MVFEKTdax1w/UserByScreenName"
    
    features = {
        "hidden_profile_likes_enabled": False,
        "hidden_profile_subscriptions_enabled": False,
        "responsive_web_graphql_exclude_directive_enabled": True,
        "verified_phone_label_enabled": False,
        "subscriptions_verification_info_is_identity_verified_enabled": True,
        "subscriptions_verification_info_verified_since_enabled": True,
        "highlights_tweets_tab_ui_enabled": True,
        "responsive_web_twitter_article_notes_tab_enabled": True,
        "creator_subscriptions_tweet_preview_api_enabled": True,
        "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
        "responsive_web_graphql_timeline_navigation_enabled": True,
        "blue_business_profile_image_shape_enabled": True
    }

    variables = {"screen_name": username, "withSafetyModeUserFields": True}
    params = {
        "variables": json.dumps(variables),
        "features": json.dumps(features)
    }
    
    try:
        r = await session.get(url, params=params)
        if r.status_code != 200:
            return None
        
        data = r.json()
        result = data.get("data", {}).get("user", {}).get("result", {})
        
        if result.get("__typename") == "UserUnavailable":
             return None

        return result.get("rest_id")
            
    except Exception:
        return None

async def main():
    async with AsyncSession(
        proxies={"http": PROXY, "https": PROXY},
        headers=headers,
        cookies=COOKIES,
        impersonate="chrome110",
        timeout=30
    ) as s:
        
        user_id = await get_user_id(s, TARGET_USERNAME)
        if not user_id:
            print("Failed to get User ID")
            return

        cursor = None
        count = 0
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            while count < LIMIT:
                url = "https://api.x.com/1.1/followers/list.json"
                params = {
                    "user_id": user_id,
                    "count": 200,
                }
                if cursor:
                    params["cursor"] = cursor

                try:
                    r = await s.get(url, params=params)
                except Exception:
                    break
                
                if r.status_code == 429:
                    await asyncio.sleep(60)
                    continue
                
                if r.status_code != 200:
                    break

                data = r.json()
                users = data.get("users", [])
                
                if not users:
                    break

                for u in users:
                    f.write(f"@{u['screen_name']}\n")
                    count += 1
                
                print(f"Collected: {count}", end="\r")
                
                cursor = data.get("next_cursor_str")
                if not cursor or cursor == "0" or cursor == 0:
                    break
                
                await asyncio.sleep(1.0)

    print(f"\nTotal: {count}")

if __name__ == "__main__":
    asyncio.run(main())