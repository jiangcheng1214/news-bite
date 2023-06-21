
import requests


headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-CA;q=0.7',
    'Cache-Control': 'max-age=0',
    'Cookie': 'region=211; language=en; currency=USD; api_uid=Cm0C+WRxuTVGzgBUnTtwAg==; timezone=Asia%2FShanghai; webp=1; _nano_fp=XpEJnpg8np9YX0TJn9_jhruiyZ_LhAp0CUThC1NQ; _bee=cEkfgPbxJUQDbpyA8ZZpRmugklMZAapT; njrpl=cEkfgPbxJUQDbpyA8ZZpRmugklMZAapT; dilx=mpZDpzFA631uO5bflomcM; hfsc=L32CfYg37D7805DEeQ==; _device_tag=CgI2WRIIWG9MU3RkbnkaMPrHb1+lHr0EUn9CJzRNSVijecCD+AfGikiT0zdE9BNdk64ZYogVSw6JgFF0lRzKnjAC; _fbp=fb.1.1685176657415.2008866876; _u_pa=%7B%22nrpt_211%22%3A0%7D; _ga=GA1.1.714357977.1685176657; sc_cache_valid=1; _gcl_au=1.1.1625695425.1685176659; shipping_city=211; g_state={"i_l":0}; cf_clearance=UHr.1Eoff4tmGtqyccRjyC670UekHZkK1CJ9XpnetdA-1685868132-0-160; user_uin=BAHJR4NGVW6E6WBDKR7WUL53AZUQ6SI5THHJ4QXG; AccessToken=WOIXKMNR2EJ3MKUL4HNO23BJFWZZIREBLLDZ3GTCJONJCIMWMW2A0110d3c439ab; isLogin=1685962594319; __cf_bm=Jul0E4RGq1oJjtrn7UbyOcSaVnTmPFpuKVpdn05HU14-1685964525-0-AdPWc31dJ2UZFyyQTW17YIBje6unCeU4yOgEqMWcCW5BoWL8u2ghqN+OBe77AZgCz4EeXWFYRwkdjqkcGB148mQ=; gtm_logger_session=iq4qm53ig9gy4luh9o7zf; _ga_R8YHFZCMMX=GS1.1.1685962181.11.1.1685964907.45.0.0',
    'Sec-Ch-Ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"macOS"',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-User': '?1',
    'Service-Worker-Navigation-Preload': 'true',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
}


url = "https://www.temu.com/api/alexa/homepage/goods_list?offset=0&count=1000&list_id=u5mso4j0996tzo25n1afy&opt_id=-1&listId=u5mso4j0996tzo25n1afy&scene=home&page_list_id=1bzojc9hpkmyx7x2cu9kx"

response = requests.get(url, headers=headers)

print(response.text)