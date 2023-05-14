# Twitter

Data aquisition based on tweets from verified twitter user and topic specific rules

## Raw data
Json for individual raw tweet including metadata from rule-based live streaming

script: `python3 src/scripts/run_forever_twitter_stream_monitor.py`

Raw data example:
(`data/tweets/{topic}/{date}/raw_{hour}`)
```
{
    "tweet": {"author_id": "1388092340225527811","created_at": "2023-03-30T07:00:00.000Z", "edit_history_tweet_ids": ["1641334445104922625"], "entities": {"hashtags": [{"start": 0, "end": 12, "tag": "XANAGenesis"}, {"start": 81, "end": 84, "tag": "AI"}, {"start": 193, "end": 198, "tag": "XANA"}, {"start": 199, "end": 209, "tag": "Metaverse"}, {"start": 210, "end": 215, "tag": "NFTs"}, {"start": 216, "end": 225, "tag": "NFTJapan"}, {"start": 226, "end": 239, "tag": "NFTCommunity"}], "urls": [{"start": 241, "end": 264, "url": "https://t.co/pJMZ6crCGt", "expanded_url": "https://opensea.io/assets/ethereum/0x5b5cf41d9ec08d101ffeeeebda411677582c9448/1236", "display_url": "opensea.io/assets/ethereu\u2026"}, {"start": 265, "end": 288, "url": "https://t.co/ne9wNtzBBT", "expanded_url": "https://twitter.com/XANAMetaverse/status/1641334445104922625/photo/1", "display_url": "pic.twitter.com/ne9wNtzBBT", "media_key": "3_1641312896964759553"}]}, "id": "1641334445104922625", "lang": "en", "text": "#XANAGenesis NFT #7691 (Katharine)\nHas traded at 0.4149 ETH\ud83d\udd25\n\nMeet this stunning #AI beauty \"Katharine\"\ud83e\udd70\n\n\u27a1\ufe0fHair: Bob Sparkle Grey\n\u27a1\ufe0fClothes: Tech Master Orange Gray\n\u27a1\ufe0fEyes: Bright Sharp Blue\n\n#XANA #Metaverse #NFTs #NFTJapan #NFTCommunity \nhttps://t.co/pJMZ6crCGt https://t.co/ne9wNtzBBT"}, "authorMetadata": {"id": "1388092340225527811", "name": "XANA", "username": "XANAMetaverse", "url": "https://t.co/7szQwX5vO1", "description": "#Metaverse x #AI technology for billions of users. Adopted by major Institutions and global brands. | Founder : @Rio_Noborderz | DAO : https://t.co/0lmaIbdb6V", "protected": false, "verified": true, "location": "Mobile / Desktop / VR", "created_at": "2021-04-30T11:26:36.000Z", "public_metrics": {"followers_count": 231142, "following_count": 20, "tweet_count": 4433, "listed_count": 317}}
}
```

## Hourly summary
Hourly tweet summary based on raw tweet data that related to specific topic.

Hourly summary data example:
(`data/tweets/{topic}/{date}/sum_{hour}`)

```
{"usage": {"prompt_tokens": 586, "total_tokens": 800, "completion_tokens": 214}, "text": "1. XANA Genesis NFT #7691 \"Katharine\" traded at 0.4149 ETH.\n2. Crypto.com is giving away US$200,000 of NUM tokens to new and existing users.\n3. AltCryptoGems shares a motivation quote: \"If you can dream it, you can do it. If you can earn it, you can buy #Bitcoin.\"\n4. BSC News shares 5 quick facts about Dogecoin.\n5. The Ethiopian government and Oromo Liberation Army are moving towards talks.\n6. Bitcoin is showing bullish signs with Crypto Rover's update.\n7. Hong Kong fund led by Ben Ng aims to raise $100 million to invest in crypto startups.\n8. McLaren expands partnership with OKX as the Official Primary Partner of the team.\n9. DustyBC Crypto shares a 10% discount code \"DUSTYBC\" for Bitcoin 2023 in Miami with a link to the tickets.\n10. No tweet related to government regulations or official announcements from authoritative sources related to crypto currency found.", "finish_reason": "stop", "turns": 1}
```

script: `python3 src/scripts/run_forever_twitter_summary_generation_hourly.py`

## Day level summary
Day level tweet summary based on hourly summary. Summary will be generated at 6am, 12pm and 6pm PST (California time). We will enrich each summary item by finding the most similar raw tweet using embedding technology so that we can get the source content link.

Summary example:
(`data/tweet_summaries/{topic}/{date}/summary_{hour}`)

```
- Shib's hourly update reveals a decrease in 24-hour market cap and token supply burn
- The BRC-20 ecosystem is continuing to soar, creating a new market narrative for cryptocurrencies
- Traders are keeping an eye on signs from Washington regarding potential market-upending defaults in the US
- The US credit market is on high alert for a debt deal or default
- G7 finance leaders are pledging to contain inflation and strengthen supply chains, urging local governments to invest in water systems
- FMCG players are battling inflation with price hikes and reductions in grammage
- Members of Congress's exceptional stock market performance has raised calls for a ban
- Municipal bonds may see a $100 billion reinvestment surge
- Biden administration is investing in infrastructure, innovation, and manufacturing to create jobs
- Interest rates remain steady in Brazil due to high levels of public debt
- Wearable robotic exoskeleton market is projected to grow to $4 billion
- FactSet reports that 78% of S&P 500 companies beat EPS estimates for Q1, above 5 and 10-year averages
- UAE launches new 5-year strategy for Higher Colleges of Technology, committed to investing in human development
- Shib's hourly update shows a decrease in 24-hour market cap and token supply burn
- Investors should remain pragmatic and “read the fine print” amid the hype and noise of ChatGPT in the Large Language Models market
- Capitalism can actually encourage environmental progress
- Defensive stocks may be overly crowded with investors amid market jitters
- G7 successfully agrees on a statement after meetings
- Uganda must refocus its efforts on boosting export earnings
```

Enriched summary example:
(`data/tweet_summaries/{topic}/{date}/summary_{hour}_enriched`)

```
{"summary": "- Municipal bonds may see a $100 billion reinvestment surge", "match_score": 0.9782637781326712, "source_text": "Municipal bonds may see a $100 billion reinvestment surge \ud83d\udcb8 ", "tweet_url": "https://twitter.com/BloombergTV/status/1657527175480766468", "unwound_url": "https://www.bloomberg.com/news/articles/2023-05-11/stock-market-today-dow-s-p-live-updates?utm_source=twitter&utm_campaign=socialflow-organic&cmpid%3D=socialflow-twitter-tv&utm_content=tv&utm_medium=social"}
{"summary": "- Wearable robotic exoskeleton market is projected to grow to $4 billion", "match_score": 0.9628730211846073, "source_text": "Global wearable robotic exoskeleton market forecasted to grow to $4 billion. (Robotics and Automation) #Robotics ", "tweet_url": "https://twitter.com/jamesvgingerich/status/1657485616316022787", "unwound_url": "http://roboticsandautomationnews.com/2019/08/31/global-wearable-robotic-exoskeleton-market-forecasted-to-grow-to-4-billion/25277/"}
{"summary": "- Defensive stocks may be overly crowded with investors amid market jitters", "match_score": 0.9569655223399378, "source_text": "Investors may be crowding too much into defensive stocks amid market jitters ", "tweet_url": "https://twitter.com/CNBC/status/1657475881512599554", "unwound_url": "https://www.cnbc.com/2023/05/13/investors-may-be-crowding-too-much-into-defensive-stocks-amid-market-jitters.html?utm_content=Main&utm_medium=Social&utm_source=Twitter"}
...
...
{"summary": "- Members of Congress's exceptional stock market performance has raised calls for a ban", "match_score": 0.87275531585985, "source_text": "2022 was the worst year for the stock market since 2008. Millions of Americans lost money, but almost every member of Congress beat the market by a considerable margin. Coincidence or conspiracy? Either way, it's time to ban members of Congress from trading stocks.", "tweet_url": "https://twitter.com/michaelrulli/status/1657536271324004353", "unwound_url": ""}
```

script: `python3 src/scripts/run_once_twitter_summary_daily.py`
