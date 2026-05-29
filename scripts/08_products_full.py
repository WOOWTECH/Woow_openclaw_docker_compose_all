#!/usr/bin/env python3
"""
Phase 8-10: Clean demo data, create categories, create products, publish on eCommerce.
Runs inside the Odoo pod.
"""
import xmlrpc.client
import base64
import json
import os
import re
import urllib.parse

url = "http://localhost:8069"
db = "inzense"
password = "admin"

common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, "admin", password, {})
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)

PRODUCTS_JSON = "/tmp/inzense_products.json"
IMAGES_DIR = "/tmp/inzense-images/products"

with open(PRODUCTS_JSON, encoding="utf-8") as f:
    products_data = json.load(f)

print(f"Loaded {len(products_data)} products from JSON")

# ================================================================
# Real product descriptions scraped from inzense.com.tw
# Key = substring that matches product name; Value = description_sale
# ================================================================
PRODUCT_DESCRIPTIONS = {
    # === 功能系列 (Functional Series) ===
    "排寒香": (
        "夢中獲得配方的啟發，透過香氣調整和測試，希望能給予使用者正能量或陽氣，排除身心靈的沉重能量和邪氣。\n\n"
        "【成分】70%香粉（綠檀、非洲降真、緬甸小葉降真、艾草）+30%印尼楠木黏粉\n"
        "【規格】長18.5cm × 直徑1.8mm，約12g，約29支\n"
        "【燃燒時間】約50分鐘（無風室內）\n"
        "【適用空間】居家、起居空間、辦公室、工作室、寺廟\n"
        "【保存方式】常溫乾燥陰涼處\n"
        "【產地】台灣製造"
    ),
    "財神香": (
        "若平日行善積德，心存善念，積極進取，使用後將快速招來財富豐盛的能量或機會。\n\n"
        "【成分】70%香粉（西澳洲檀香根部、非洲降真檀、伊利安沉香、秘魯聖木、伊朗玫瑰）+30%印尼楠木黏粉\n"
        "【規格】長18.5cm × 直徑1.8mm，約10g，約34支\n"
        "【燃燒時間】約50分鐘（無風室內）\n"
        "【適用空間】居家、辦公室、店面、寺廟\n"
        "【原料產地】西澳、非洲、印尼、秘魯、伊朗\n"
        "【產地】台灣製造"
    ),
    "善緣香": (
        "增加貴人運和事業運，聚合善緣，讓身邊的人際關係更加和諧美好。\n\n"
        "【規格】長17-18.5cm × 直徑1.8mm，約30支\n"
        "【燃燒時間】約40-50分鐘（無風室內）\n"
        "【適用空間】居家、起居空間、辦公室\n"
        "【保存方式】常溫乾燥陰涼處\n"
        "【產地】台灣製造"
    ),
    "除障香": (
        "溫暖的雪松和艾草香氣，能量由內而外、由下而上地驅散寒氣。多種天然香材的調和，創造出平順、放鬆且穩定的整體體驗，專為排除個人障礙而設計。\n\n"
        "【成分】紫檀、非洲降真檀、緬甸降真、巴拉圭綠檀、西澳檀香根、柬埔寨沉香、台灣肖楠、台灣黃檜、台灣龍柏、台灣香樟、秘魯聖木、白色鼠尾草、美國雪松、台灣香茅、澳洲茶樹、琥珀、紅安息香\n"
        "【規格】長18.5cm × 直徑1.8mm，約12g，約29支\n"
        "【燃燒時間】約50分鐘（無風室內）\n"
        "【適用空間】居家、辦公室、工作室、寺廟\n"
        "【產地】台灣製造"
    ),
    "十方清淨": (
        "古色古香，整體香氣的調性在放鬆中保持清淨。一種讓身心沉靜、安息的柔和平衡，悄悄地進入心神，達到意識漸漸放空的作用。冥想時使用可大幅減少雜念。\n\n"
        "【成分】柬埔寨沉香、越南惠安沉香、加里萬丹沉香、古邦老山檀香、黑安息香、香草安息香\n"
        "【規格】長18.5cm × 直徑1.8mm，約10g，約26支\n"
        "【燃燒時間】約50分鐘（無風室內）\n"
        "【適用空間】居家、辦公室、工作室、佛堂\n"
        "【產地】台灣製造"
    ),
    "壇城樂土": (
        "混合不同產地的降真與沉香，這兩種原料都是植物受傷後形成的保護機制，蘊含強大的淨化與安定能量。\n\n"
        "【成分】非洲降真檀香、緬甸降真、伊利安沉香\n"
        "【規格】約9g，約24支\n"
        "【燃燒時間】約50分鐘（無風室內）\n"
        "【產地】台灣製造"
    ),
    "靈感香": (
        "激發創意覺醒、思緒通透、靈感對頻，適合需要靈感與創意的時刻使用。\n\n"
        "【成分】70%香粉（泰國沉香、委內瑞拉紫檀、琥珀、香草安息香）+30%印尼楠木黏粉\n"
        "【燃燒時間】約50分鐘（無風室內）\n"
        "【產地】台灣製造"
    ),
    "療心香": (
        "以多種珍貴檀香與沉香調製，搭配玫瑰的療癒香氣，讓心靈得到溫柔的撫慰與修復。\n\n"
        "【成分】紫檀、巴拉圭綠檀、非洲降真檀香、西澳洲新山檀香根部、馬拉OK沉香、越南惠安沉香、相思樹、玫瑰+印尼楠木黏粉\n"
        "【產地】台灣製造"
    ),
    "三清檀香": (
        "取名「三清」，意即身心靈三者的清明。除了帶來身心靈清明，也能渡化人心。先是聖木的香氣，如一個溫暖的防護。\n\n"
        "【成分】70%香粉（西澳洲檀香根部、秘魯聖木等）+30%印尼楠木黏粉\n"
        "【燃燒時間】約50分鐘（無風室內）\n"
        "【產地】台灣製造"
    ),
    "正龍沉香": (
        "以台灣本土龍柏與肖楠，搭配柬埔寨沉香與秘魯聖木，帶來幽遠靜謐的放鬆感。\n\n"
        "【成分】秘魯聖木、台灣龍柏、台灣肖楠、柬埔寨沉香\n"
        "【規格】約9g，約29支\n"
        "【燃燒時間】約50分鐘（無風室內）\n"
        "【產地】台灣製造"
    ),
    "放鬆香": (
        "以多種頂級檀香與乳香調製，帶來深層放鬆與舒壓的香氛體驗。\n\n"
        "【成分】西澳檀香根、緬甸降真、非洲降真檀香、阿曼皇家乳香、神聖沒藥、神聖安息香、紅安息香\n"
        "【規格】長18.5cm × 直徑2.5mm\n"
        "【產地】台灣製造"
    ),
    "平安香": (
        "多種天然香材融合，帶來平安祥和的能量，適合祈求出行平安、家宅安穩時使用。\n\n"
        "【成分】巴拉圭綠檀、西澳檀香根、秘魯聖木、雪松、白色鼠尾草、澳洲茶樹、依蘭花、梔子花、玫瑰花、神聖安息香、阿曼乳香\n"
        "【產地】台灣製造"
    ),
    "幸運香": (
        "為想增加一些幸運能量與自信心的您而設計，開啟好運的鑰匙。\n\n"
        "【成分】巴拉圭綠檀、台灣黃檜、台灣牛樟、秘魯聖木、橙花、雪松、玫瑰花、紅安息香、龍血、阿拉伯乳香、印尼楠木黏粉\n"
        "【產地】台灣製造"
    ),
    "姻緣香": (
        "以多種珍貴花卉與檀香調製，為有緣人帶來姻緣牽引的美好祝福。\n\n"
        "【成分】巴拉圭綠檀、紫檀、非洲降真檀香、西澳洲新山檀香根部、古邦老山檀香、伊利安沉香、馬拉OK沉香、玫瑰花、依蘭依蘭花、梔子花\n"
        "【產地】台灣製造"
    ),

    # === 神明系列 (Deity Series) ===
    "觀世音菩薩": (
        "觀世音菩薩 — 結善良緣之香\n"
        "化作慈悲的輕語，一縷香煙，輕撫焦慮，傳遞願望，讓香氣承載祝福與護佑。\n\n"
        "香氣層次：\n"
        "前調：淡雅柔和的木質調，彷彿慈悲的溫暖\n"
        "中調：清涼如水的草藥香，帶來淨化與生機\n"
        "後調：細膩的樹脂甜韻，最溫暖的撫慰\n"
        "整體：輕柔、香甜卻不會過於甜膩、淡雅又如風一般清爽\n\n"
        "【成分】上等老山檀香（印度老山檀香精華、古邦老山檀香、西澳新山檀香調和）、非洲降真檀、白安息香、印尼楠木黏粉\n"
        "【適用時機】心懷憂慮渴望慰藉時、為家人祈福守護平安時、空間注入柔和安定能量時\n"
        "【產地】台灣製造"
    ),
    "財神爺": (
        "財神爺 — 財運增益之香\n"
        "點燃這支香，感受財富能量的聚合，為事業與財運帶來穩固的加持。\n\n"
        "【適用時機】招財增加業績、開運求財時\n"
        "【產地】台灣製造"
    ),
    "關聖帝君": (
        "關聖帝君 — 忠義護佑之香\n"
        "義薄雲天的關聖帝君，守護正義與是非，為事業提供堅強的戰力加持。\n\n"
        "【適用時機】需要正義守護、事業拓展時\n"
        "【產地】台灣製造"
    ),
    "天上聖母": (
        "天上聖母 — 安寧庇護之香\n"
        "一縷香煙，將安寧送到你牽掛的每一個方向。媽祖的慈悲與守護，帶來出行平安與心靈安定。\n\n"
        "【適用時機】祈求出行平安、母性守護時\n"
        "【產地】台灣製造"
    ),
    "福德正神": (
        "福德正神 — 厚德庇佑之香\n"
        "土地公的厚德之力，守護家宅安穩、地運亨通，帶來穩固的根基能量。\n\n"
        "【適用時機】祈求家宅安穩、事業穩固時\n"
        "【產地】台灣製造"
    ),
    "月老星君": (
        "月老星君 — 姻緣牽引之香\n"
        "月下老人的紅線，牽引有緣人相遇，為感情帶來圓滿與幸福。\n\n"
        "【適用時機】祈求姻緣、增進感情時\n"
        "【產地】台灣製造"
    ),
    "藥師佛": (
        "藥師佛 — 身體安康之香\n"
        "藥師琉璃光如來的加持，為身心帶來安康與療癒的能量。\n\n"
        "【適用時機】祈求身體健康、病痛消除時\n"
        "【產地】台灣製造"
    ),
    "玉皇上帝": (
        "玉皇上帝 — 天道庇佑之香\n"
        "庇佑平安、迎來好運，感受生活中的天道守護。\n\n"
        "【適用時機】祈求全面庇佑、重大決策時\n"
        "【產地】台灣製造"
    ),
    "佛祖": (
        "釋迦摩尼佛 — 結善良緣之香\n"
        "佛祖的智慧光明，照亮前路，帶來內心的安定與清明。\n\n"
        "【適用時機】修行靜心、祈求智慧時\n"
        "【產地】台灣製造"
    ),
    "釋迦摩尼佛": (
        "釋迦摩尼佛 — 結善良緣之香\n"
        "佛祖的智慧光明，照亮前路，帶來內心的安定與清明。\n\n"
        "【適用時機】修行靜心、祈求智慧時\n"
        "【產地】台灣製造"
    ),
    "文昌帝君": (
        "文昌帝君 — 智慧亨通之香\n"
        "為你開啟靈感與智慧之門，學業加持、心境清明。\n\n"
        "【適用時機】考試進修、學業精進時\n"
        "【產地】台灣製造"
    ),
    "玄天上帝": (
        "玄天上帝 — 鎮煞護正之香\n"
        "讓沉穩檀香化為無形護盾，鎮煞驅邪、守護正氣。\n\n"
        "【適用時機】需要驅邪避煞、空間淨化時\n"
        "【產地】台灣製造"
    ),
    "城隍爺": (
        "城隍爺 — 避邪消災之香\n"
        "城隍爺的威嚴之力，化解災厄、守護平安。\n\n"
        "【適用時機】祈求消災解厄、辟邪護身時\n"
        "【產地】台灣製造"
    ),
    "註生娘娘": (
        "註生娘娘 — 迎福納喜之香\n"
        "守護孕期順利、母子平安，迎接新生命的喜悅。\n\n"
        "【適用時機】祈求生育順利、添丁旺宅時\n"
        "【產地】台灣製造"
    ),
    "九天玄女": (
        "九天玄女 — 靈慧啟明之香\n"
        "九天玄女的靈慧之力，開啟直覺與洞察力。\n\n"
        "【適用時機】需要靈感、增進直覺力時\n"
        "【產地】台灣製造"
    ),
    "中壇元帥": (
        "中壇元帥 — 勇毅護佑之香\n"
        "三太子的勇毅之力，守護正義、驅邪避煞。\n\n"
        "【適用時機】需要勇氣與守護力時\n"
        "【產地】台灣製造"
    ),
    "閻羅王": (
        "閻羅王 — 降伏煩惱之香\n"
        "閻羅王的威嚴力量，幫助降伏內心煩惱，業力轉化。\n\n"
        "【適用時機】化解業力、斷除煩惱時\n"
        "【產地】台灣製造"
    ),
    "純陽祖師": (
        "純陽祖師 — 護身辟邪之香\n"
        "呂洞賓的仙道之力，護身辟邪、增添福運。\n\n"
        "【適用時機】護身辟邪、修道養性時\n"
        "【產地】台灣製造"
    ),
    "降龍羅漢": (
        "降龍羅漢 — 降伏煩惱之香\n"
        "濟公的灑脫智慧，降伏塵世煩惱，帶來豁達與自在。\n\n"
        "【適用時機】化解煩惱、尋求豁達時\n"
        "【產地】台灣製造"
    ),

    # === 脈輪系列 (Chakra Series) ===
    "根輪香": (
        "對應海底輪，帶來穩定與安全感的基礎能量。\n\n"
        "【成分】非洲降真、緬甸降真、印度老山檀香、西澳新山檀香、琥珀\n"
        "【規格】長18.5cm × 直徑2.5mm，約10g，約20-30支\n"
        "【產地】台灣製造"
    ),
    "丹田輪香": (
        "對應本我輪，激發創造力與熱情的能量。\n\n"
        "【成分】非洲降真、緬甸降真、柬埔寨沉香、馬拉OK沉香\n"
        "【規格】長18.5cm × 直徑2.5mm，約10g\n"
        "【產地】台灣製造"
    ),
    "太陽輪香": (
        "對應太陽神經叢，增強自信與個人力量的能量。\n\n"
        "【成分】非洲降真、緬甸降真、西澳新山檀香小綜、西澳新山檀香樹頭、柬埔寨沉香、大黃\n"
        "【規格】長18.5cm × 直徑2.5mm，約10g\n"
        "【產地】台灣製造"
    ),
    "心輪香": (
        "對應心輪，帶來愛與同理心的療癒能量。\n\n"
        "【成分】紫檀、委內瑞拉紫檀、南美洲檀香、西澳新山檀香根部、越南惠安沉香、捲桂、花米、橙花、岩蘭草、岩玫瑰葉、公丁香\n"
        "【規格】長18.5cm × 直徑2.5mm，約10g\n"
        "【產地】台灣製造"
    ),
    "喉輪香": (
        "對應喉輪，促進溝通表達與自我表現的能量。\n\n"
        "【成分】馬拉OK沉香、甘松、大黃、凌香、大茴香、香附子、公丁香、玫瑰\n"
        "【規格】長18.5cm × 直徑2.5mm，約10g\n"
        "【產地】台灣製造"
    ),
    "眉心輪香": (
        "對應第三眼，提升直覺與洞察力，帶來思緒清明。\n\n"
        "【成分】柬埔寨沉香、甘草、花米\n"
        "【規格】長18.5cm × 直徑2.5mm，約10g\n"
        "【產地】台灣製造"
    ),
    "頂輪香": (
        "對應頂輪，連結高層意識與靈性覺醒的能量。\n\n"
        "【成分】紫檀、柬埔寨沉香、泰國沉香、加里萬丹沉香、排草、細辛、藿香、花椒\n"
        "【規格】長18.5cm × 直徑2.5mm，約10g\n"
        "【產地】台灣製造"
    ),

    # === 五行系列 (Five Elements Series) ===
    "金神香": (
        "五行金元素，補充金行能量，帶來肅穆與收斂的力量。\n\n"
        "【規格】長18.5cm × 直徑2.5mm，約10g\n"
        "【產地】台灣製造"
    ),
    "木神香": (
        "五行木元素，補充木行能量，帶來生發與成長的力量。\n\n"
        "【規格】長18.5cm × 直徑2.5mm，約10g\n"
        "【產地】台灣製造"
    ),
    "水神香": (
        "五行水元素，補充水行能量，帶來智慧與流動的力量。\n\n"
        "【規格】長18.5cm × 直徑2.5mm，約10g\n"
        "【產地】台灣製造"
    ),
    "火神香": (
        "五行火元素，補充火行能量，帶來熱情與行動的力量。\n\n"
        "【規格】長18.5cm × 直徑2.5mm，約10g\n"
        "【產地】台灣製造"
    ),
    "土神香": (
        "五行土元素，補充土行能量，帶來穩定與包容的力量。\n\n"
        "【規格】長18.5cm × 直徑2.5mm，約10g\n"
        "【產地】台灣製造"
    ),

    # === 台灣系列 (Taiwan Series) ===
    "台灣肖楠": (
        "台灣特有的珍貴樹種，香味稀少珍貴，每款皆帶有台灣的歷史痕跡。\n\n"
        "【成分】台灣肖楠香粉+印尼楠木黏粉\n"
        "【產地】台灣製造"
    ),
    "台灣黄檜": (
        "台灣特有的珍貴檜木，散發獨特的清新木質香氣，帶有台灣山林的原始氣息。\n\n"
        "【成分】黄檜香粉+印尼楠木黏粉\n"
        "【產地】台灣製造"
    ),
    "台灣龍柏": (
        "台灣在地龍柏，散發穩重而沉靜的木質香調。\n\n"
        "【成分】龍柏香粉+印尼楠木黏粉\n"
        "【產地】台灣製造"
    ),
    "台灣牛樟": (
        "台灣特有的珍貴牛樟木，帶有獨特的樟腦清香。\n\n"
        "【成分】牛樟香粉+印尼楠木黏粉\n"
        "【產地】台灣製造"
    ),
    "台灣香茅": (
        "台灣在地香茅草，散發清新的草本香氣，驅蚊避邪。\n\n"
        "【成分】台灣香茅香粉+印尼楠木黏粉\n"
        "【產地】台灣製造"
    ),
    "台灣香樟": (
        "台灣本土香樟木，帶有沉穩而清雅的樟木香氣。\n\n"
        "【成分】台灣香樟香粉+印尼楠木黏粉\n"
        "【產地】台灣製造"
    ),

    # === 外國系列 (International Series) ===
    "澳洲茶樹": (
        "來自澳洲的天然茶樹，帶有清新的草本氣息，具淨化與提神之效。\n\n"
        "【成分】澳洲茶樹香粉+印尼楠木黏粉\n"
        "【產地】台灣製造"
    ),
    "白色鼠尾草": (
        "白色鼠尾草是北美原住民神聖的淨化植物，具有強大的空間淨化能量。\n\n"
        "【成分】白色鼠尾草香粉+印尼楠木黏粉\n"
        "【產地】台灣製造"
    ),
    "秘魯聖木": (
        "來自南美洲的神聖木材 Palo Santo，具有淨化空間、提升靈性的獨特功效。\n\n"
        "【成分】秘魯聖木香粉+印尼楠木黏粉\n"
        "【產地】台灣製造"
    ),
    "美國杜松": (
        "來自美國的杜松木，帶有清新的松脂香氣，寧心安神。\n\n"
        "【成分】美國杜松香粉+印尼楠木黏粉\n"
        "【產地】台灣製造"
    ),
    "美國雪松": (
        "來自美國的雪松木，散發溫暖穩重的木質香調，帶來沉穩安定的氛圍。\n\n"
        "【成分】美國雪松香粉+印尼楠木黏粉\n"
        "【產地】台灣製造"
    ),

    # === 檀香系列 (Sandalwood Series) ===
    "琥珀巴西紫檀": (
        "安神定魄的松香味，加上讓循環活絡的特殊當歸香氣。\n\n"
        "【成分】琥珀紫檀+當歸\n"
        "【產地】台灣製造"
    ),
    "琥珀紫檀": (
        "安神定魄的松香味，加上讓循環活絡的特殊當歸香氣。\n\n"
        "【成分】琥珀紫檀+當歸\n"
        "【規格】1尺3，約290粗支\n"
        "【產地】台灣製造"
    ),
    "上等老山檀香": (
        "精選上等老山檀香，散發溫醇厚實的經典檀香韻味。\n\n"
        "【成分】上等老山檀香香粉+印尼楠木黏粉\n"
        "【產地】台灣製造"
    ),
    "巴拉圭綠檀": (
        "柔順香甜和沉穩的飽和感，帶有淡淡的輕甜檸檬香、奶香、微醺的木質香氣。\n\n"
        "【成分】70%香粉（巴拉圭綠檀）+30%印尼楠木黏粉\n"
        "【產地】台灣製造"
    ),
    "古邦老山檀香": (
        "溫暖濃郁的奶香和醇厚的檸檬香，多層次的豐富變化。正印尼古邦產地的頂級老山檀香。\n\n"
        "【成分】70%香粉（古邦老山檀香）+30%印尼楠木黏粉\n"
        "【產地】台灣製造"
    ),
    "印度老山檀香": (
        "正印度老山檀香，散發最經典醇厚的檀香韻味，為檀香中的極品。\n\n"
        "【成分】70%香粉（印度老山檀香）+30%印尼楠木黏粉\n"
        "【燃燒時間】約40分鐘（無風室內）\n"
        "【產地】台灣製造"
    ),
    "特A老山檀香": (
        "精選特A等級老山檀香，品質優異，香韻悠長。\n\n"
        "【成分】特A老山檀香香粉+印尼楠木黏粉\n"
        "【規格】長18.5cm × 直徑2.5mm，約10g\n"
        "【產地】台灣製造"
    ),
    "西澳新山檀香大綜": (
        "西澳洲產新山檀香大綜部位，香氣飽滿醇厚。\n\n"
        "【成分】西澳洲新山檀香大綜香粉+印尼楠木黏粉\n"
        "【產地】台灣製造"
    ),
    "西澳新山檀香根部": (
        "西澳洲產新山檀香根部，根部含油量最高，香氣最為濃郁持久。\n\n"
        "【成分】70%香粉（西澳洲檀香根部）+30%印尼楠木黏粉\n"
        "【燃燒時間】約40分鐘（無風室內）\n"
        "【產地】台灣製造"
    ),
    "西澳新山檀香頭部": (
        "西澳洲產新山檀香頭部，頭部香氣清揚高雅。\n\n"
        "【成分】西澳洲新山檀香頭部香粉+印尼楠木黏粉\n"
        "【產地】台灣製造"
    ),

    # === 沉香系列 (Agarwood Series) ===
    "馬拉OK": (
        "馬拉OK產地土沉香，散發獨特的東南亞沉香韻味。\n\n"
        "【產地】台灣製造"
    ),
    "加里萬丹": (
        "加里萬丹產地土沉香，適合供佛、空間芳香與淨化心靈。\n\n"
        "【成分】70%香粉+30%印尼楠木黏粉\n"
        "【用途】供佛、空間芳香、淨化心靈\n"
        "【產地】台灣製造"
    ),
    "安汶": (
        "安汶產地土沉香，帶有獨特的島嶼沉香香韻。\n\n"
        "【成分】安汶沉香粉+印尼楠木黏粉\n"
        "【產地】台灣製造"
    ),
    "巴布亞": (
        "巴布亞產地土沉香，帶有豐富的熱帶沉香氣息。\n\n"
        "【成分】巴布亞沉香粉+印尼楠木黏粉\n"
        "【產地】台灣製造"
    ),
    "柬埔寨土沉香": (
        "野生品種沉香的豐富韻味，配上紫檀木的當歸甘甜香氣，幽遠靜謐中帶來放鬆和舒適感。\n\n"
        "【成分】柬埔寨沉香粉+印尼楠木黏粉\n"
        "【產地】台灣製造"
    ),
    "泰國水沉香": (
        "泰國產水沉香，適合供佛、空間芳香與淨化心靈。\n\n"
        "【成分】70%香粉+30%印尼楠木黏粉\n"
        "【用途】供佛、空間芳香、淨化心靈\n"
        "【產地】台灣製造"
    ),
    "越南惠安沉香": (
        "越南惠安產地沉香，散發經典的惠安沉香清雅韻味。\n\n"
        "【成分】越南惠安沉香粉+印尼楠木黏粉\n"
        "【產地】台灣製造"
    ),

    # === 特色系列 (Signature Series) ===
    "碧兒花香": (
        "特別以啤酒原料來製作，帶有啤酒花香氣，放鬆舒壓。\n\n"
        "【成分】非洲降真、啤酒花、阿曼乳香等\n"
        "【規格】長18.5cm × 直徑2.5mm\n"
        "【產地】台灣製造"
    ),
    "貓醉香": (
        "專為貓咪愛好者設計的獨特線香，以貓薄荷與木天蓼等天然貓草材料製作，人貓共享的放鬆時光。\n\n"
        "【成分】西澳洲檀香根、貓薄荷、蟲癭果實粉、木天蓼果實粉、木天蓼野生原葉、木天蓼細枝\n"
        "【規格】長18.5cm × 直徑2.5mm\n"
        "【產地】台灣製造"
    ),

    # === 拜拜用香 (Worship Incense) ===
    "柬埔寨沉香": (
        "野生品種沉香的豐富韻味，配上紫檀木的當歸甘甜香氣，幽遠靜謐中帶來放鬆和舒適感。\n\n"
        "【產地】台灣製造"
    ),
    "非洲降真檀香": (
        "非洲降真檀香，散發獨特的降真木香韻，適合日常拜拜與空間淨化。\n\n"
        "【產地】台灣製造"
    ),
    "野生泰國沉香": (
        "野生泰國沉香，品質珍稀，散發醇厚悠遠的沉香韻味。\n\n"
        "【產地】台灣製造"
    ),
}

def get_product_description(name):
    """Match product name to a detailed description from the website."""
    for key, desc in PRODUCT_DESCRIPTIONS.items():
        if key in name:
            return desc
    return ""


# ================================================================
# EAN-13 barcode generation (471 = Taiwan, 0001 = Inzense)
# ================================================================
def ean13_check_digit(code12):
    """Calculate EAN-13 check digit for a 12-digit string."""
    total = 0
    for i, ch in enumerate(code12):
        total += int(ch) * (1 if i % 2 == 0 else 3)
    return str((10 - (total % 10)) % 10)


def make_ean13(seq):
    """Generate EAN-13 barcode: 471 + 0001 + 5-digit seq + check digit."""
    code12 = f"471000{seq:06d}"
    return code12 + ean13_check_digit(code12)


barcode_seq = 0  # global counter for barcode assignment

# ================================================================
# STEP 1: Clean demo product data
# ================================================================
print("\n" + "=" * 60)
print("STEP 1: Clean demo data")
print("=" * 60)

# Delete demo products (English ones from Odoo demo data)
demo_products = models.execute_kw(db, uid, password, "product.template", "search", [
    [["name", "not ilike", "線香"],
     ["name", "not ilike", "迷你香"],
     ["name", "not ilike", "香品"],
     ["name", "not ilike", "inzense"],
     ["name", "not ilike", "禪香"],
     ["create_uid", "=", 1],  # created by admin/system (demo)
    ]
], {"limit": 500})

if demo_products:
    # First unpublish from website
    try:
        models.execute_kw(db, uid, password, "product.template", "write", [demo_products, {
            "website_published": False,
            "sale_ok": False,
        }])
    except:
        pass
    print(f"Unpublished {len(demo_products)} demo products from website")
else:
    print("No demo products to clean")

# Delete demo public categories (keep our custom ones)
our_cat_names = [
    "線香", "迷你香", "拜拜用香", "原木筆", "優惠組合",
    "神明系列", "功能系列", "脈輪系列", "五行系列", "外國系列",
    "台灣系列", "特色系列", "降真系列", "檀香系列", "沉香系列",
    "福石手串", "會員專區",
]
demo_cats = models.execute_kw(db, uid, password, "product.public.category", "search", [
    [["name", "not in", our_cat_names]]
])
if demo_cats:
    try:
        models.execute_kw(db, uid, password, "product.public.category", "unlink", [demo_cats])
        print(f"Deleted {len(demo_cats)} demo public categories")
    except Exception as e:
        print(f"Could not delete demo categories: {e}")

print("Demo data cleanup done")

# ================================================================
# STEP 2: Create/update product public categories
# ================================================================
print("\n" + "=" * 60)
print("STEP 2: Create product categories")
print("=" * 60)

website_id = 1

def get_or_create_category(name, parent_id=False):
    """Get or create a product.public.category."""
    domain = [["name", "=", name]]
    if parent_id:
        domain.append(["parent_id", "=", parent_id])
    existing = models.execute_kw(db, uid, password, "product.public.category", "search", [domain])
    if existing:
        return existing[0]
    cat_id = models.execute_kw(db, uid, password, "product.public.category", "create", [{
        "name": name,
        "parent_id": parent_id if parent_id else False,
        "website_id": website_id,
    }])
    print(f"  Created category: {name} (parent={parent_id}) -> ID={cat_id}")
    return cat_id

# Top-level categories
cat_long = get_or_create_category("線香")
cat_mini = get_or_create_category("迷你香")
cat_worship = get_or_create_category("拜拜用香")
cat_pen = get_or_create_category("原木筆")
cat_combo = get_or_create_category("優惠組合")
cat_bracelet = get_or_create_category("福石手串")
cat_member = get_or_create_category("會員專區")

# Sub-categories for 線香 and 迷你香
series_names = ["神明系列", "功能系列", "脈輪系列", "五行系列", "外國系列",
                "台灣系列", "特色系列", "降真系列", "檀香系列", "沉香系列"]

long_sub = {}
mini_sub = {}
for series in series_names:
    long_sub[series] = get_or_create_category(series, cat_long)
    mini_sub[series] = get_or_create_category(series, cat_mini)

# Combo sub-categories
combo_names = ["馬年有喜新春開運組", "神明保庇熱賣組", "上班創業必備組", "內在穩定能量組", "脈輪療癒優惠組"]
combo_sub = {}
for cn in combo_names:
    combo_sub[cn] = get_or_create_category(cn, cat_combo)

print(f"Categories setup complete")

# ================================================================
# STEP 3: Map category names from scraped data to Odoo IDs
# ================================================================
def map_categories(product_categories):
    """Map scraped category strings to Odoo public category IDs."""
    cat_ids = set()
    cat_str = " ".join(product_categories).lower()

    # Check for 迷你香 first (before 線香 check, since some have both)
    is_mini = "迷你香" in cat_str
    is_long = "線香" in cat_str and not is_mini

    if is_mini:
        cat_ids.add(cat_mini)
        for series in series_names:
            if series in cat_str:
                cat_ids.add(mini_sub[series])
    elif is_long:
        cat_ids.add(cat_long)
        for series in series_names:
            if series in cat_str:
                cat_ids.add(long_sub[series])

    if "拜拜用香" in cat_str or "拜拜" in cat_str:
        cat_ids.add(cat_worship)
    if "原木筆" in cat_str:
        cat_ids.add(cat_pen)
    if "福石" in cat_str or "手串" in cat_str:
        cat_ids.add(cat_bracelet)
    if "優惠" in cat_str or "組合" in cat_str:
        cat_ids.add(cat_combo)
        for cn in combo_names:
            if cn in cat_str:
                cat_ids.add(combo_sub[cn])
    if "會員" in cat_str:
        cat_ids.add(cat_member)

    return list(cat_ids) if cat_ids else [cat_long]  # default to 線香

# ================================================================
# STEP 4: Upload product images and create products
# ================================================================
print("\n" + "=" * 60)
print("STEP 4: Create products with images")
print("=" * 60)

# Preload image filename mapping from URLs
def url_to_filename(img_url):
    """Convert URL to local filename."""
    parsed = urllib.parse.urlparse(img_url)
    fname = urllib.parse.unquote(os.path.basename(parsed.path))
    return fname

def upload_image(filepath, name):
    """Upload image file as ir.attachment, return attachment ID."""
    if not os.path.isfile(filepath):
        return False
    fsize = os.path.getsize(filepath)
    if fsize < 100:  # skip tiny/empty files
        return False
    with open(filepath, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    ext = os.path.splitext(filepath)[1].lower()
    mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".gif": "image/gif"}
    mimetype = mime_map.get(ext, "image/jpeg")
    att_id = models.execute_kw(db, uid, password, "ir.attachment", "create", [{
        "name": name,
        "datas": data,
        "type": "binary",
        "mimetype": mimetype,
        "public": True,
    }])
    return att_id

created_count = 0
skipped_count = 0
error_count = 0

for i, prod in enumerate(products_data):
    name = prod["name"]
    if not name or len(name) < 2:
        skipped_count += 1
        continue

    # Check if product already exists
    existing = models.execute_kw(db, uid, password, "product.template", "search", [
        [["name", "=", name]]
    ])
    if existing:
        skipped_count += 1
        continue

    # Map categories
    pub_cat_ids = map_categories(prod.get("categories", []))

    # Determine price
    price = prod.get("price", 0)
    sale_price = prod.get("sale_price", 0)
    list_price = price if price > 0 else 999  # default price

    # Upload main image
    main_image_data = False
    extra_image_ids = []

    for j, img_url in enumerate(prod.get("images", [])):
        fname = url_to_filename(img_url)
        filepath = os.path.join(IMAGES_DIR, fname)
        if not os.path.isfile(filepath):
            continue
        if os.path.getsize(filepath) < 100:
            continue

        with open(filepath, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()

        if j == 0:
            # Main product image
            main_image_data = img_b64
        else:
            # Extra images
            extra_image_ids.append(img_b64)

    # Create product
    try:
        # Use real website description if available, fallback to scraped description
        real_desc = get_product_description(name)
        sale_desc = real_desc if real_desc else prod.get("description", "")

        # Assign sequential barcode and internal reference
        barcode_seq += 1
        product_barcode = make_ean13(barcode_seq)
        product_ref = f"INZ-{barcode_seq:03d}"

        vals = {
            "name": name,
            "list_price": list_price,
            "type": "consu",
            "sale_ok": True,
            "purchase_ok": True,
            "website_published": False,  # We'll publish later
            "public_categ_ids": [(6, 0, pub_cat_ids)],
            "description_sale": sale_desc,
            "barcode": product_barcode,
            "default_code": product_ref,
        }
        if main_image_data:
            vals["image_1920"] = main_image_data

        if sale_price > 0 and sale_price < list_price:
            vals["list_price"] = sale_price
            # We'd need a pricelist for the original price, but for now use compare_list_price
            vals["compare_list_price"] = list_price

        prod_id = models.execute_kw(db, uid, password, "product.template", "create", [vals])

        # Add extra images as product.image records
        for k, extra_b64 in enumerate(extra_image_ids[:4]):  # max 4 extra images
            try:
                models.execute_kw(db, uid, password, "product.image", "create", [{
                    "name": f"{name} - {k+2}",
                    "image_1920": extra_b64,
                    "product_tmpl_id": prod_id,
                }])
            except:
                pass

        created_count += 1
        if created_count % 20 == 0:
            print(f"  Created {created_count} products... (current: {name[:40]})")
        if created_count <= 5 or created_count % 10 == 0:
            print(f"    {product_ref} | {product_barcode} | {name[:45]}")
    except Exception as e:
        error_count += 1
        if error_count <= 5:
            print(f"  ERROR creating '{name[:40]}': {e}")

print(f"\nProducts created: {created_count}")
print(f"Products skipped (existing): {skipped_count}")
print(f"Errors: {error_count}")

# ================================================================
# STEP 5: Publish all products on eCommerce website
# ================================================================
print("\n" + "=" * 60)
print("STEP 5: Publish products on eCommerce")
print("=" * 60)

# Get all our products (non-demo ones with Chinese names)
all_prods = models.execute_kw(db, uid, password, "product.template", "search", [
    ["|", "|", "|", "|", "|",
     ["name", "ilike", "線香"],
     ["name", "ilike", "迷你香"],
     ["name", "ilike", "香品"],
     ["name", "ilike", "系列"],
     ["name", "ilike", "組合"],
     ["name", "ilike", "香"],
    ]
], {"limit": 500})

if all_prods:
    models.execute_kw(db, uid, password, "product.template", "write", [all_prods, {
        "website_published": True,
        "is_published": True,
        "sale_ok": True,
    }])
    print(f"Published {len(all_prods)} products on eCommerce website")

# Set website for all public categories
all_pub_cats = models.execute_kw(db, uid, password, "product.public.category", "search", [[]])
if all_pub_cats:
    models.execute_kw(db, uid, password, "product.public.category", "write", [all_pub_cats, {
        "website_id": website_id,
    }])
    print(f"Set website for {len(all_pub_cats)} public categories")

# Verify
total_published = models.execute_kw(db, uid, password, "product.template", "search_count", [
    [["website_published", "=", True]]
])
print(f"\nTotal published products on website: {total_published}")

# Verify shop page
import urllib.request
try:
    resp = urllib.request.urlopen("http://localhost:8069/shop")
    print(f"Shop page: HTTP {resp.status}")
except Exception as e:
    print(f"Shop page error: {e}")

print("\n=== Phase 8-10 COMPLETE ===")
