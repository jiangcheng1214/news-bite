import requests
from bs4 import BeautifulSoup
import mysql.connector
from urllib.parse import urlparse


# 创建数据库连接
cnx = mysql.connector.connect(user='root', password='MyN3wP4ssw0rd',
                              host='localhost',
                              database='temu')

# 创建游标对象
cursor = cnx.cursor()

headers = {
    'Method': 'GET',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-CA;q=0.7',
    'Cache-Control': 'max-age=0',
    'Cookie': 'region=211; language=en; currency=USD; api_uid=Cm0C+WRxuTVGzgBUnTtwAg==; timezone=Asia%2FShanghai; webp=1; _nano_fp=XpEJnpg8np9YX0TJn9_jhruiyZ_LhAp0CUThC1NQ; _bee=cEkfgPbxJUQDbpyA8ZZpRmugklMZAapT; njrpl=cEkfgPbxJUQDbpyA8ZZpRmugklMZAapT; dilx=mpZDpzFA631uO5bflomcM; hfsc=L32CfYg37D7805DEeQ==; _device_tag=CgI2WRIIWG9MU3RkbnkaMPrHb1+lHr0EUn9CJzRNSVijecCD+AfGikiT0zdE9BNdk64ZYogVSw6JgFF0lRzKnjAC; _fbp=fb.1.1685176657415.2008866876; _u_pa=%7B%22nrpt_211%22%3A0%7D; _ga=GA1.1.714357977.1685176657; sc_cache_valid=1; _gcl_au=1.1.1625695425.1685176659; shipping_city=211; g_state={"i_l":0}; AccessToken=QHBT6CCYNPDY3UCPIRK3T5UVUMJ3LA6VYREGWM72UY7S5FGOPC7A0110d3c43a13; user_uin=BAHJR4NGVW6E6WBDKR7WUL53AZUQ6SI5THHJ4QXG; isLogin=1685847149678; cf_clearance=UHr.1Eoff4tmGtqyccRjyC670UekHZkK1CJ9XpnetdA-1685868132-0-160; gtm_logger_session=7gf8bfhalp5n7wy98a99r; goods=goods_sq00sc; __cf_bm=Tjc0xM4NoXaqt5Dn6H1wcsJnZNdvDvefVvBo7XTWMBI-1685870522-0-AR6tjKwoEnKUC5aE4ayUYYL+f3b2nf/h2ZeiyQJcbsj/hKG3IBIFk1bmoqOmiVGY8fQsDf3ASYEZjDYuL0rdXpY=; _ga_R8YHFZCMMX=GS1.1.1685868144.6.1.1685870958.58.0.0',
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

url = "https://www.temu.com/womens-jumpsuits-o3-1035.html"
response = requests.get(url, headers=headers)

soup = BeautifulSoup(response.text, 'html.parser')

# 找到商品列表
goods_list = soup.find('div', {'class': '_2hynzFts autoFitList'})

# 找到每个商品
goods = goods_list.find_all('div', {'class': '_3GizL2ou'})

for good in goods:
    # 获取商品标题
    title = good.find('h2', {'class': '_2XmIMTf3'}).text
    print('Title:', title)

    # 获取主图url
    try:
        main_image_url = good.find('img')['src']
    except KeyError:
        main_image_url = None
    print('Main Image URL:', main_image_url)


    # 获取原价
    original_price = good.find('div', {'class': '_1iQkQ22o'}).text.replace('$', '')
    original_price = float(original_price) if original_price else None
    print('Original Price:', original_price)

    # 获取折扣价
    discount_price = good.find('div', {'class': '_2L24asES'}).text.replace('$', '')
    discount_price = float(discount_price) if discount_price else None
    print('Discount Price:', discount_price)

    # 获取销量
    sales = good.find('span', {'data-type': 'saleTips'}).text
    sales = sales.replace('sold', '')
    print('Sales:', sales)

    # 获取好评数
    rating_element = good.find('span', {'class': '_25MPYpvP'})
    if rating_element is None:
        rating = 0
    else:
        rating = int(rating_element.text.replace('(', '').replace(')', '').replace(',', ''))

    # 获取产品url
    # product_url = good.find('a', {'class': '_3VEjS46S _2IVkRQY-'})['href']
    a_tag = good.find('a')
    if a_tag is not None:
        product_url = a_tag['href']
    else:
        product_url = None

    print('Product URL:', product_url)

    # 解析URL并从路径中提取产品ID
    url_parts = urlparse(product_url)
    product_id = url_parts.path.split('-')[-1].replace('.html', '')
    print('Product ID:', product_id)

    print('---')

    # 插入数据的SQL语句
    add_product = ("INSERT INTO products "
                   "(title, main_image_url, original_price, discount_price, sales, rating, product_url, id) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)")

    # 商品数据
    data_product = (title, main_image_url, original_price, discount_price, sales, rating, product_url, product_id)

    # 插入数据
    cursor.execute(add_product, data_product)


# 提交事务
cnx.commit()

# 关闭游标和连接``
cursor.close()
cnx.close()
