"""
景点数据增强脚本 - 为每个景点添加5大咨询场景的详细信息
"""
import json
import os
import copy
from typing import Optional

DATA_DIR = os.path.join(os.path.dirname(__file__))
DATA_FILE = os.path.join(DATA_DIR, "attractions.json")


def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ========== 省/市级别的交通、美食、文化基础信息 ==========

PROVINCE_INFO = {
    "北京": {
        "transport_city": "北京首都国际机场/大兴国际机场、北京站/北京西站/北京南站",
        "food_base": "北京烤鸭、涮羊肉、炸酱面、豆汁儿焦圈、卤煮火烧",
        "culture_base": "京味文化、胡同文化、京剧",
    },
    "上海": {
        "transport_city": "上海浦东国际机场/虹桥国际机场、上海站/虹桥站",
        "food_base": "小笼包、生煎包、红烧肉、大闸蟹、排骨年糕",
        "culture_base": "海派文化、石库门风情、弄堂文化",
    },
    "天津": {
        "transport_city": "天津滨海国际机场、天津站/天津西站",
        "food_base": "狗不理包子、十八街麻花、耳朵眼炸糕、煎饼果子",
        "culture_base": "津门文化、曲艺之乡（相声、快板）",
    },
    "重庆": {
        "transport_city": "重庆江北国际机场、重庆西站/重庆北站",
        "food_base": "重庆火锅、小面、酸辣粉、毛血旺、辣子鸡",
        "culture_base": "巴渝文化、山城文化、码头文化",
    },
    "河北": {
        "transport_city": "正定国际机场/秦皇岛北戴河机场",
        "food_base": "驴肉火烧、河北炒饼、保定糖葫芦、承德杏仁茶",
        "culture_base": "燕赵文化、直隶文化",
    },
    "山西": {
        "transport_city": "太原武宿国际机场、太原站/太原南站",
        "food_base": "刀削面、平遥牛肉、莜面栲栳栳、太谷饼、汾酒",
        "culture_base": "晋商文化、佛教文化、面食文化",
    },
    "内蒙古": {
        "transport_city": "呼和浩特白塔国际机场",
        "food_base": "手把肉、烤全羊、奶茶、奶皮子、莜面",
        "culture_base": "蒙古族游牧文化、那达慕大会、马头琴",
    },
    "辽宁": {
        "transport_city": "沈阳桃仙国际机场/大连周水子国际机场",
        "food_base": "东北饺子、锅包肉、小鸡炖蘑菇、烤冷面、海鲜",
        "culture_base": "满族文化、工业文化、关东文化",
    },
    "吉林": {
        "transport_city": "长春龙嘉国际机场",
        "food_base": "吉林冷面、朝鲜族打糕、人参鸡、乌拉火锅",
        "culture_base": "朝鲜族文化、雾凇文化、汽车工业文化",
    },
    "黑龙江": {
        "transport_city": "哈尔滨太平国际机场",
        "food_base": "锅包肉、哈尔滨红肠、马迭尔冰棍、杀猪菜、铁锅炖",
        "culture_base": "冰雪文化、俄罗斯风情、东北民俗",
    },
    "江苏": {
        "transport_city": "南京禄口国际机场/苏南硕放国际机场",
        "food_base": "盐水鸭、鸭血粉丝汤、大煮干丝、蟹粉汤包、松鼠鳜鱼",
        "culture_base": "吴文化、金陵文化、江南水乡文化",
    },
    "浙江": {
        "transport_city": "杭州萧山国际机场",
        "food_base": "西湖醋鱼、东坡肉、龙井虾仁、绍兴黄酒、宁波汤圆",
        "culture_base": "吴越文化、江南文化、茶文化",
    },
    "安徽": {
        "transport_city": "合肥新桥国际机场/黄山屯溪国际机场",
        "food_base": "徽菜（臭鳜鱼、毛豆腐）、黄山烧饼、淮南牛肉汤",
        "culture_base": "徽州文化、文房四宝、徽商文化",
    },
    "福建": {
        "transport_city": "福州长乐国际机场/厦门高崎国际机场",
        "food_base": "佛跳墙、沙县小吃、土笋冻、海蛎煎、武夷岩茶",
        "culture_base": "闽南文化、客家文化、妈祖文化",
    },
    "江西": {
        "transport_city": "南昌昌北国际机场",
        "food_base": "南昌拌粉、瓦罐汤、鄱阳湖鱼头、景德镇瓷器",
        "culture_base": "赣文化、陶瓷文化、红色文化",
    },
    "山东": {
        "transport_city": "济南遥墙国际机场/青岛胶东国际机场",
        "food_base": "煎饼卷大葱、德州扒鸡、青岛啤酒、烟台苹果、周村烧饼",
        "culture_base": "齐鲁文化、儒家文化、泰山文化",
    },
    "河南": {
        "transport_city": "郑州新郑国际机场",
        "food_base": "烩面、胡辣汤、灌汤包、道口烧鸡、洛阳水席",
        "culture_base": "中原文化、河洛文化、少林文化",
    },
    "湖北": {
        "transport_city": "武汉天河国际机场",
        "food_base": "热干面、武昌鱼、鸭脖、三鲜豆皮、排骨藕汤",
        "culture_base": "楚文化、三国文化、荆楚民俗",
    },
    "湖南": {
        "transport_city": "长沙黄花国际机场",
        "food_base": "臭豆腐、剁椒鱼头、辣椒炒肉、湘西腊肉、米粉",
        "culture_base": "湖湘文化、湘西苗族文化、楚文化",
    },
    "广东": {
        "transport_city": "广州白云国际机场/深圳宝安国际机场",
        "food_base": "粤式点心（虾饺、烧卖）、烧鹅、白切鸡、煲仔饭、双皮奶",
        "culture_base": "广府文化、潮汕文化、岭南文化",
    },
    "广西": {
        "transport_city": "南宁吴圩国际机场/桂林两江国际机场",
        "food_base": "桂林米粉、螺蛳粉、老友粉、啤酒鱼、荔浦芋扣肉",
        "culture_base": "壮族文化、刘三姐文化、山水文化",
    },
    "海南": {
        "transport_city": "海口美兰国际机场/三亚凤凰国际机场",
        "food_base": "文昌鸡、椰子饭、清补凉、海鲜、热带水果",
        "culture_base": "黎苗文化、热带海岛文化、南洋文化",
    },
    "四川": {
        "transport_city": "成都天府国际机场/双流国际机场",
        "food_base": "火锅、串串香、担担面、麻婆豆腐、回锅肉、夫妻肺片",
        "culture_base": "巴蜀文化、川剧变脸、茶文化、大熊猫文化",
    },
    "贵州": {
        "transport_city": "贵阳龙洞堡国际机场",
        "food_base": "酸汤鱼、花溪牛肉粉、肠旺面、丝娃娃、茅台酒",
        "culture_base": "苗族文化、侗族文化、酒文化",
    },
    "云南": {
        "transport_city": "昆明长水国际机场/丽江三义国际机场",
        "food_base": "过桥米线、汽锅鸡、野生菌火锅、宣威火腿、鲜花饼",
        "culture_base": "傣族文化、纳西文化、白族文化、彝族文化",
    },
    "西藏": {
        "transport_city": "拉萨贡嘎国际机场、青藏铁路",
        "food_base": "酥油茶、糌粑、牦牛肉、藏面、青稞酒",
        "culture_base": "藏传佛教文化、藏族民俗、唐卡艺术",
    },
    "陕西": {
        "transport_city": "西安咸阳国际机场、西安站/西安北站",
        "food_base": "肉夹馍、羊肉泡馍、凉皮、Biangbiang面、葫芦鸡",
        "culture_base": "周秦汉唐文化、丝绸之路文化、关中民俗",
    },
    "甘肃": {
        "transport_city": "兰州中川国际机场、兰州站",
        "food_base": "兰州牛肉面、酿皮、手抓羊肉、杏皮水、百合",
        "culture_base": "丝路文化、敦煌文化、多民族文化",
    },
    "青海": {
        "transport_city": "西宁曹家堡国际机场、青藏铁路",
        "food_base": "青海酸奶、手抓羊肉、酿皮、甜醅、青稞饼",
        "culture_base": "藏族文化、伊斯兰文化、高原文化",
    },
    "宁夏": {
        "transport_city": "银川河东国际机场",
        "food_base": "手抓羊肉、羊杂碎、羊肉搓面、硒砂瓜、枸杞",
        "culture_base": "西夏文化、回族文化、黄河文化",
    },
    "新疆": {
        "transport_city": "乌鲁木齐地窝堡国际机场",
        "food_base": "烤羊肉串、大盘鸡、抓饭、拉条子、馕、葡萄干",
        "culture_base": "维吾尔族文化、哈萨克族文化、丝绸之路文化",
    },
    "香港": {
        "transport_city": "香港国际机场、高铁西九龙站",
        "food_base": "烧腊、云吞面、丝袜奶茶、蛋挞、煲仔饭、叉烧",
        "culture_base": "中西合璧文化、粤语文化、电影文化",
    },
    "澳门": {
        "transport_city": "澳门国际机场、港珠澳大桥",
        "food_base": "葡式蛋挞、猪扒包、水蟹粥、杏仁饼、葡国菜",
        "culture_base": "中葡文化融合、博彩文化、历史城区文化",
    },
    "台湾": {
        "transport_city": "桃园国际机场/台北松山机场",
        "food_base": "牛肉面、蚵仔煎、珍珠奶茶、凤梨酥、卤肉饭",
        "culture_base": "闽南文化、原住民文化、当代文创文化",
    },
}


# ========== 景点级别的详细信息 ==========

def gen_basic_info(att: dict) -> str:
    """生成基础信息"""
    name = att["name"]
    province = att["province"]
    category = att["category"]

    info_parts = [f"📍 {att.get('city', '')}{name}"]
    if "开放时间" not in info_parts:
        if category == "历史文化" or "寺" in name or "庙" in name or "宫" in name:
            info_parts.append("🕐 开放时间：旺季 08:00-17:30，淡季 08:30-17:00（具体以景区公告为准）")
        elif category == "自然风光":
            info_parts.append("🕐 开放时间：通常 08:00-17:00，部分山区景区受天气影响可能调整")
        elif category == "主题乐园":
            info_parts.append("🕐 开放时间：通常 09:00-21:00，周末和节假日延长营业")
        elif category == "现代建筑":
            info_parts.append("🕐 开放时间：通常 09:00-22:00")
        elif category == "都市风情":
            info_parts.append("🕐 开放时间：全天开放")
        else:
            info_parts.append("🕐 开放时间：请查询景区官方公告")

    info_parts.append(f"🎫 门票价格：{att.get('ticket', '请查询官方信息')}")
    info_parts.append(f"⏱ 建议游玩：{'3-4小时' if category in ['历史文化', '现代建筑'] else '半天至一天' if category == '自然风光' else '2-3小时' if category == '都市风情' else '一天'}")

    if province in PROVINCE_INFO:
        info_parts.append(f"🚗 如何到达：{PROVINCE_INFO[province]['transport_city']}")

    return "  \n".join(info_parts)


def gen_travel_guide(att: dict) -> str:
    """生成游玩攻略"""
    name = att["name"]
    category = att["category"]
    best_season = att.get("best_season", "全年皆宜")

    guide = [f"📅 **最佳季节**：{best_season}"]

    if category == "历史文化":
        guide.append("🎯 **游览重点**：建议提前了解相关历史背景，可请导游讲解或租用讲解器，会更有收获")
        guide.append("👣 **推荐路线**：核心建筑→专题展馆→园林/附属建筑，重点观赏标志性建筑和珍贵文物")
    elif category == "自然风光":
        guide.append("🎯 **游览重点**：建议乘坐索道/观光车先到最高点俯瞰全景，再步行下山细赏")
        guide.append("👣 **推荐路线**：索道上山→山顶观景→步行下山→沿途景点打卡")
        guide.append("🎒 **装备建议**：穿舒适登山鞋，带足饮用水，防晒用品，雨具")
    elif category == "主题乐园":
        guide.append("🎯 **游玩策略**：开园前到达，先玩最热门的项目，利用单人通道减少排队")
        guide.append("👣 **推荐路线**：热门项目优先→表演/巡游→其他项目→烟花/灯光秀")
    elif category == "都市风情":
        guide.append("🎯 **游览重点**：建议白天和夜晚各游览一次，感受不同的城市氛围")
        guide.append("👣 **推荐路线**：主要地标打卡→特色街区漫步→夜景欣赏")
    else:
        guide.append("🎯 **游览重点**：可根据个人兴趣和时间灵活安排")

    guide.append(f"💡 **温馨提示**：{att.get('tips', '出行前建议查询景区最新公告')}")

    # 季节特别提醒
    season_tips = {
        "夏季": "夏季注意防晒防暑，建议早晨或傍晚出行，多补充水分",
        "冬季": "冬季注意保暖防寒，部分景区可能因天气关闭部分区域",
        "春季": "春季天气多变，建议携带雨具和外套",
        "秋季": "秋季气候宜人，但昼夜温差大，建议带一件外套",
    }
    for season, tip in season_tips.items():
        if season in best_season:
            guide.append(f"🌡️ **{season}特别提醒**：{tip}")
            break

    return "  \n".join(guide)


def gen_transport(att: dict) -> str:
    """生成交通住宿信息"""
    name = att["name"]
    province = att["province"]
    category = att["category"]

    parts = []

    if province in PROVINCE_INFO:
        parts.append(f"✈️ **外部交通**：{PROVINCE_INFO[province]['transport_city']}")
    else:
        parts.append("✈️ **外部交通**：建议查询当地机场或高铁站信息")

    # 市内交通建议
    if "古" in name or "镇" in name or "村" in name:
        parts.append("🚌 **当地交通**：可乘坐旅游专线巴士或打车前往，景区内建议步行游览")
    elif "山" in name or category == "自然风光":
        parts.append("🚌 **当地交通**：市区有旅游专线巴士，景区内有观光车/索道")
    elif category == "主题乐园":
        parts.append("🚌 **当地交通**：市区有地铁/专线巴士直达，建议乘坐公共交通")
    elif "市区" in name or "中心" in name:
        parts.append("🚌 **当地交通**：位于市中心，可乘坐地铁/公交/出租车到达")
    else:
        parts.append("🚌 **当地交通**：可乘坐旅游专线或打车前往")

    # 住宿建议
    if category == "自然风光" or "山" in name:
        parts.append("🏨 **住宿推荐**：景区周边有民宿和酒店，旺季建议提前1-2周预订。山上住宿条件有限但可以看日出")
    elif "古" in name or "镇" in name:
        parts.append("🏨 **住宿推荐**：建议住在古镇内的特色民宿，体验当地风情，也能避开白天游客高峰")
    elif province in ["北京", "上海", "广州", "深圳"]:
        parts.append("🏨 **住宿推荐**：建议选择地铁沿线酒店，出行方便。市中心酒店价格较高")
    elif category == "主题乐园":
        parts.append("🏨 **住宿推荐**：可选择主题乐园官方酒店（通常含早享入园权益）或周边经济型酒店")
    else:
        parts.append("🏨 **住宿推荐**：景区周边有多种住宿选择，建议根据预算选择")

    return "  \n".join(parts)


def gen_food(att: dict) -> str:
    """生成美食特产信息"""
    name = att["name"]
    province = att["province"]
    category = att["category"]
    city = att.get("city", "")

    parts = []

    if province in PROVINCE_INFO:
        parts.append(f"🍜 **特色美食**：{PROVINCE_INFO[province]['food_base']}")
    else:
        parts.append("🍜 **特色美食**：当地有多种特色美食值得尝试")

    # 景点附近美食推荐
    if category == "历史文化" or "古" in name:
        parts.append("🏪 **美食街区**：景区周边通常有特色美食街，可品尝当地小吃，但价格可能偏高")
    elif category == "都市风情":
        parts.append("🏪 **美食街区**：周边商业区有丰富的餐饮选择，从街头小吃到高档餐厅应有尽有")
    elif "山" in name:
        parts.append("🏪 **美食街区**：山脚下通常有农家乐和特色餐厅，可品尝当地农家菜")
    else:
        parts.append("🏪 **美食街区**：景区周边和市区都有丰富的美食选择")

    # 特产推荐
    area_specialties = {
        "北京": "Beijing: 北京特产包括景泰蓝、北京绢人、二锅头酒、稻香村糕点",
        "上海": "Shanghai: 上海特产有五香豆、梨膏糖、上海丝绸、老凤祥首饰",
        "江苏": "Jiangsu: 苏州丝绸、苏绣、南京云锦、宜兴紫砂壶",
        "浙江": "Zhejiang: 杭州丝绸、龙井茶、绍兴黄酒、金华火腿",
        "安徽": "Anhui: 徽墨、歙砚、宣纸、祁门红茶",
        "福建": "Fujian: 武夷岩茶、福州脱胎漆器、厦门馅饼",
        "江西": "Jiangxi: 景德镇瓷器、庐山云雾茶、南丰蜜桔",
        "山东": "Shandong: 青岛啤酒、潍坊风筝、淄博陶瓷、东阿阿胶",
        "四川": "Sichuan: 蜀绣、郫县豆瓣、蒙顶茶、张飞牛肉",
        "云南": "Yunnan: 普洱茶、云南白药、鲜花饼、扎染布艺",
        "陕西": "Shaanxi: 陕北大枣、西凤酒、剪纸、皮影",
        "甘肃": "Gansu: 兰州百合、夜光杯、洮砚、敦煌地毯",
        "新疆": "Xinjiang: 和田玉、葡萄干、哈密瓜、天山雪莲",
    }
    if province in area_specialties:
        parts.append(f"🎁 **当地特产**：{area_specialties[province]}")

    return "  \n".join(parts)


def gen_culture(att: dict) -> str:
    """生成民俗文化信息"""
    name = att["name"]
    province = att["province"]
    category = att["category"]

    parts = []

    if province in PROVINCE_INFO:
        parts.append(f"📖 **地域文化**：{PROVINCE_INFO[province]['culture_base']}")
    else:
        parts.append("📖 **地域文化**：当地有丰富的文化传统和民俗风情")

    # 历史文化景点的深度文化信息
    if category == "历史文化":
        if "寺" in name or "庙" in name:
            parts.append("🙏 **宗教文化**：参观寺院/庙宇时请注意着装得体，保持安静，尊重宗教习俗。拍照前注意是否有禁止拍摄标识")
        elif "石窟" in name:
            parts.append("🎨 **艺术价值**：石窟艺术是佛教艺术与中国传统艺术的结合，建议提前了解相关历史背景")
        elif "古" in name or "城" in name:
            parts.append("🏛️ **建筑特色**：古建筑是中国传统建筑艺术的精华，注意观察斗拱、藻井、彩绘等细节")
        elif "园" in name:
            parts.append("🌿 **园林艺术**：中国古典园林讲究借景、对景、框景等手法，体现了天人合一的哲学思想")
        else:
            parts.append("🏛️ **文化价值**：作为历史文化景点，承载着丰富的历史记忆和文化内涵")
    elif category == "自然风光":
        parts.append("🏔️ **山水文化**：中国传统文化中'仁者乐山，智者乐水'，山水之间蕴含深厚的文化意境")
    elif category == "主题乐园":
        parts.append("🎉 **主题文化**：主题乐园融合了娱乐、科技和文化体验，适合各年龄段游客")
    elif category == "现代建筑":
        parts.append("🏗️ **建筑文化**：现代建筑体现了当代工程技术和高超的设计理念，是城市发展的见证")

    # 节庆活动
    festivals = {
        "北京": "春节庙会（地坛/龙潭湖）、中秋赏月（颐和园/北海公园）",
        "江苏": "南京秦淮灯会（春节期间）、苏州园林文化节",
        "浙江": "杭州西湖博览会、钱塘江观潮节（农历八月十八）",
        "四川": "成都国际熊猫节、自贡灯会",
        "云南": "泼水节（傣族/4月中旬）、火把节（彝族/农历六月二十四）",
        "湖南": "湘西苗族赶秋节、端午节汨罗江龙舟赛",
        "广西": "壮族三月三歌圩节、桂林山水旅游节",
        "西藏": "藏历新年、雪顿节（藏历六月）",
        "陕西": "西安丝绸之路国际旅游博览会、延安红色旅游节",
        "内蒙古": "那达慕大会（7-8月）",
        "新疆": "古尔邦节、肉孜节、喀什噶尔国际文化旅游节",
        "贵州": "苗族姊妹节、侗族大歌节",
        "福建": "妈祖诞辰（农历三月二十三）、闽南文化节",
        "河南": "洛阳牡丹文化节（4月）、少林武术节",
    }
    if province in festivals:
        parts.append(f"🎊 **特色节庆**：{festivals[province]}")

    return "  \n".join(parts)


def enhance_attraction(att: dict) -> dict:
    """为单个景点添加5大咨询场景字段"""
    enhanced = copy.deepcopy(att)

    enhanced["basic_info"] = gen_basic_info(att)
    enhanced["travel_guide"] = gen_travel_guide(att)
    enhanced["transport"] = gen_transport(att)
    enhanced["food"] = gen_food(att)
    enhanced["culture"] = gen_culture(att)

    return enhanced


def main():
    data = load_data()
    print(f"已加载 {len(data)} 个景点")

    enhanced = [enhance_attraction(a) for a in data]
    save_data(enhanced)

    # 验证
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        verified = json.load(f)

    first = verified[0]
    new_fields = ["basic_info", "travel_guide", "transport", "food", "culture"]
    for field in new_fields:
        assert field in first, f"缺少字段: {field}"

    print(f"增强完成！共 {len(verified)} 个景点，每个新增 {len(new_fields)} 个信息字段")
    print(f"样例行：{first['name']}")
    print(f"  basic_info: {first['basic_info'][:50]}...")
    print(f"  travel_guide: {first['travel_guide'][:50]}...")
    print(f"  transport: {first['transport'][:50]}...")
    print(f"  food: {first['food'][:50]}...")
    print(f"  culture: {first['culture'][:50]}...")


if __name__ == "__main__":
    main()
