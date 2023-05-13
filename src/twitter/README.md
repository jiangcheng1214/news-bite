# Twitter

Data aquisition based on tweets from verified twitter user and topic specific rules

## Raw data
Json for individual tweet including metadata from rule-based live streaming
For example, the following rule is set for "crypto currency" related tweets:

    {
        "value": "(bitcoin OR btc OR #bitcoin OR #btc OR eth2 OR ethereum2 OR ethereum OR eth OR #ethereum OR #ethereum2 OR #eth OR #eth2 OR crypto OR \"crypto currency\" OR \"block chain\" OR blockchain OR #crypto OR #cryptocurrency OR #blockchain) -#airdrop -#airdrops -#giveaway -#giveaways -airdrop -giveaway -retweet -\"like or retweet\" -\"retweet or like\" -\"retweet this\" -\"rt/like\" -\"like/rt\" -\"follow me\" -\"give away\" -\"sign up\" -\"for free\" -is:retweet -is:reply -is:quote lang:en is:verified followers_count:100000",
        "tag": "crypto_currency"
    }


script: `python3 src/scripts/run_forever_twitter_stream_monitor.py`

data example (line per json/tweet):

```
{
    "tweet": {"author_id": "1388092340225527811","created_at": "2023-03-30T07:00:00.000Z", "edit_history_tweet_ids": ["1641334445104922625"], "entities": {"hashtags": [{"start": 0, "end": 12, "tag": "XANAGenesis"}, {"start": 81, "end": 84, "tag": "AI"}, {"start": 193, "end": 198, "tag": "XANA"}, {"start": 199, "end": 209, "tag": "Metaverse"}, {"start": 210, "end": 215, "tag": "NFTs"}, {"start": 216, "end": 225, "tag": "NFTJapan"}, {"start": 226, "end": 239, "tag": "NFTCommunity"}], "urls": [{"start": 241, "end": 264, "url": "https://t.co/pJMZ6crCGt", "expanded_url": "https://opensea.io/assets/ethereum/0x5b5cf41d9ec08d101ffeeeebda411677582c9448/1236", "display_url": "opensea.io/assets/ethereu\u2026"}, {"start": 265, "end": 288, "url": "https://t.co/ne9wNtzBBT", "expanded_url": "https://twitter.com/XANAMetaverse/status/1641334445104922625/photo/1", "display_url": "pic.twitter.com/ne9wNtzBBT", "media_key": "3_1641312896964759553"}]}, "id": "1641334445104922625", "lang": "en", "text": "#XANAGenesis NFT #7691 (Katharine)\nHas traded at 0.4149 ETH\ud83d\udd25\n\nMeet this stunning #AI beauty \"Katharine\"\ud83e\udd70\n\n\u27a1\ufe0fHair: Bob Sparkle Grey\n\u27a1\ufe0fClothes: Tech Master Orange Gray\n\u27a1\ufe0fEyes: Bright Sharp Blue\n\n#XANA #Metaverse #NFTs #NFTJapan #NFTCommunity \nhttps://t.co/pJMZ6crCGt https://t.co/ne9wNtzBBT"}, "authorMetadata": {"id": "1388092340225527811", "name": "XANA", "username": "XANAMetaverse", "url": "https://t.co/7szQwX5vO1", "description": "#Metaverse x #AI technology for billions of users. Adopted by major Institutions and global brands. | Founder : @Rio_Noborderz | DAO : https://t.co/0lmaIbdb6V", "protected": false, "verified": true, "location": "Mobile / Desktop / VR", "created_at": "2021-04-30T11:26:36.000Z", "public_metrics": {"followers_count": 231142, "following_count": 20, "tweet_count": 4433, "listed_count": 317}}
}
```

## Hourly summary
Hourly tweet summary based on clean data. 1 to N mapping to clean data. Summarization is done via AI. As we know AI is more like a black box, we can only control over prompt and will leverage human knowledge for verification on every AI version release.

data example (one "sum_*" file per hourly summary):
```
{"usage": {"prompt_tokens": 586, "total_tokens": 800, "completion_tokens": 214}, "text": "1. XANA Genesis NFT #7691 \"Katharine\" traded at 0.4149 ETH.\n2. Crypto.com is giving away US$200,000 of NUM tokens to new and existing users.\n3. AltCryptoGems shares a motivation quote: \"If you can dream it, you can do it. If you can earn it, you can buy #Bitcoin.\"\n4. BSC News shares 5 quick facts about Dogecoin.\n5. The Ethiopian government and Oromo Liberation Army are moving towards talks.\n6. Bitcoin is showing bullish signs with Crypto Rover's update.\n7. Hong Kong fund led by Ben Ng aims to raise $100 million to invest in crypto startups.\n8. McLaren expands partnership with OKX as the Official Primary Partner of the team.\n9. DustyBC Crypto shares a 10% discount code \"DUSTYBC\" for Bitcoin 2023 in Miami with a link to the tickets.\n10. No tweet related to government regulations or official announcements from authoritative sources related to crypto currency found.", "finish_reason": "stop", "turns": 1}
```

script: `python3 src/scripts/run_forever_twitter_summary_generation_hourly.py`

## Daily summary
Daily tweet summary based on hourly summary. 1 to N mapping to hourly summary data. Similar to hourly summary, this is done via AI. Houly summaries are grouped due to token 4096 limit per AI processing, thus, daily summaries can be more than one for each day. Each summary contains at most 20 items.

data example (one "daily_sum.json" file per daily summary):
```
{"usage": {"prompt_tokens": 3018, "total_tokens": 3384, "completion_tokens": 366}, "text": "1. Bitfinex invests in renewable Bitcoin mining in El Salvador, calls for other companies to invest in Bitcoin development.\n2. Intain modernizes asset-backed securities with Avalanche Subnets.\n3. SolidProof.io offers educational resources to learn about crypto security.\n4. Successful WomeninCrypto event in South Africa discusses Web3 and blockchain.\n5. PwC Germany collaborates with Chainlink to scale up blockchain adoption for enterprises and capital markets.\n6. Rarible partners with Polygon zkEVM to support Ethereum and other blockchains.\n7. The Tie launches a compliant messaging app for crypto-hungry institutions.\n8. BlackRock issues a Fed warning after a huge Bitcoin and Ethereum boom.\n9. Only 16% of Ethereum is staked, in contrast to other cryptocurrencies.\n10. Galaxy Digital founder Michael Novogratz thinks crypto prices are rising despite government crackdown thanks to an \"energized\" investor base.\n11. Ledger secures $108M to strengthen hardware crypto wallets.\n12. Bloomberg explores whether banks are deliberately blocking crypto companies.\n13. SEC chairman Gensler highlights need for new tools and resources to combat misconduct in crypto.\n14. Phantom wallet is compatible with apps on Ethereum, Polygon, and Solana.\n15. Bitmain shares tips on how to get the world's first hashrate NFT and sell hashrate on-chain through PizzaNFT.\n16. Elizabeth Warren's plan to become US President includes killing Bitcoin.\n17. Denmark\u2019s Supreme Court rules that bitcoin profits are taxable.\n18. Ethereum deflation is heating up, according to Lark Davis.\n19. Bitcoin briefly tops $29,000 despite US Commodity Futures Trading Commission's crackdown on Binance.\n20. Bitcoin reaches its highest level since June, possibly due to uncertainty in the banking sector.", "finish_reason": "stop", "turns": 1}
```

script: `python3 src/scripts/run_once_twitter_summary_daily.py`

## Daily summary enrichment
Daily tweet summary enrichment with data source information. We embed both raw contents and summarization items and map raw info to summarization based on semantic similarity (greater dot product between two text embedding means more similar).


data example (one "daily_sum_enriched.json" file per enriched daily summary):
```
{"summary": "8. BlackRock issues a Fed warning after a huge Bitcoin and Ethereum boom.", "source_text": "Crypto Price Alert: BlackRock Issues Stark Fed Warning After Huge Bitcoin And Ethereum Boom ", "tweet_url": "https://twitter.com/Forbes/status/1641511917544955912", "unwound_url": "https://www.forbes.com/sites/digital-assets/2023/03/30/crypto-price-alert-blackrock-issues-stark-fed-warning-after-huge-bitcoin-and-ethereum-boom/?sh=faea0985ddc9&utm_source=ForbesMainTwitter&utm_medium=social&utm_campaign=socialflowForbesMainTwitter"}
{"summary": "9. Only 16% of Ethereum is staked, in contrast to other cryptocurrencies.", "source_text": "71% of #Cardano is staked 70% of #Solana is staked 85% of #BNB Chain is staked 63% of #AVAX is staked 50% of #Polkadot is staked 37% of #MATIC is staked 64% of #Cosmos is staked Only 16% of #Ethereum is staked. How much will this change after Shanghai upgrade?", "tweet_url": "https://twitter.com/AltcoinDailyio/status/1641512289110200320", "unwound_url": ""}
{"summary": "10. Galaxy Digital founder Michael Novogratz thinks crypto prices are rising despite government crackdown thanks to an \"energized\" investor base.", "source_text": "Galaxy Digital founder Michael Novogratz says that thanks to an \"energized\" investor base, crypto prices are rising despite government crackdown on the industry ", "tweet_url": "https://twitter.com/crypto/status/1641514839498448910", "unwound_url": "https://www.bloomberg.com/news/articles/2023-03-30/novogratz-says-energized-crypto-btc-fans-negate-crackdown-damage?utm_source=twitter&utm_campaign=socialflow-organic&utm_content=crypto&utm_medium=social"}
```

script: `python3 src/scripts/run_once_enrich_twitter_summary_daily.py`