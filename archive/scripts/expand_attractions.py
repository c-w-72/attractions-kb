"""
景点数据批量扩充脚本
将 105 个景点扩充至约 300 个，覆盖所有省份和分类
"""

import json
import os
import sys

DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                         "data", "attractions.json")

EXPANSIONS = [
    # ===== 北京（补充） =====
    {"name": "鸟巢（国家体育场）", "province": "北京", "city": "北京", "category": "现代建筑",
     "description": "2008年北京奥运会主体育场，以其独特的钢结构设计闻名于世，是现代建筑史上的标志性作品。", "highlights": "外观拍照、奥运回忆展、空中走廊",
     "best_season": "四季皆宜", "tips": "夜景尤其美丽，建议傍晚前往。", "rating": 4.5, "ticket": "50元"},
    {"name": "水立方（国家游泳中心）", "province": "北京", "city": "北京", "category": "现代建筑",
     "description": "2008年奥运会游泳比赛场馆，外观似水滴状蓝色气泡，梦幻而科技感十足。", "highlights": "奥运泳池、水上乐园、冬奥冰壶场地",
     "best_season": "四季皆宜", "tips": "与鸟巢相邻，可一同游览。", "rating": 4.4, "ticket": "30元"},
    {"name": "恭王府", "province": "北京", "city": "北京", "category": "历史文化",
     "description": "清代规模最大的一座王府，曾为和珅宅邸，素有'一座恭王府，半部清朝史'之称。", "highlights": "后花园、大戏楼、福字碑",
     "best_season": "春秋两季", "tips": "建议请讲解介绍历史背景。", "rating": 4.6, "ticket": "40元"},
    {"name": "北海公园", "province": "北京", "city": "北京", "category": "自然风光",
     "description": "中国现存最古老、最完整的皇家园林之一，以白塔、琼华岛和太液池构成山水画卷。", "highlights": "白塔、九龙壁、琼华岛、五龙亭",
     "best_season": "3-5月、9-11月", "tips": "可以划船，湖上视角看白塔很美。", "rating": 4.6, "ticket": "10元"},
    {"name": "国家博物馆", "province": "北京", "city": "北京", "category": "历史文化",
     "description": "世界上单体建筑面积最大的博物馆，藏品数量约140万件，汇集了中国古代文物精华。", "highlights": "古代中国展厅、复兴之路、青铜器馆",
     "best_season": "四季皆宜", "tips": "免费参观，需提前预约，周一闭馆。", "rating": 4.7, "ticket": "免费"},

    # ===== 上海（补充） =====
    {"name": "东方明珠塔", "province": "上海", "city": "上海", "category": "现代建筑",
     "description": "上海地标性建筑，高468米的电视塔，位于浦东陆家嘴，是俯瞰上海全景的最佳地点之一。", "highlights": "观光层、透明悬空廊、历史陈列馆",
     "best_season": "四季皆宜", "tips": "建议傍晚登塔，可同时欣赏日景和夜景。", "rating": 4.5, "ticket": "199元"},
    {"name": "南京路步行街", "province": "上海", "city": "上海", "category": "都市风情",
     "description": "中国最著名的商业街之一，百年老街融合了老上海风情与现代商业气息，被誉为\"中华第一商业街\"。", "highlights": "老字号店铺、和平饭店、第一百货",
     "best_season": "四季皆宜", "tips": "晚上霓虹灯亮起时最有气氛。", "rating": 4.4, "ticket": "免费"},
    {"name": "田子坊", "province": "上海", "city": "上海", "category": "都市风情",
     "description": "上海弄堂文化的代表，由石库门老建筑改造而成的创意艺术区，遍布特色小店和艺术工作室。", "highlights": "弄堂文化、艺术画廊、创意小店",
     "best_season": "四季皆宜", "tips": "周末人很多，建议工作日前往。", "rating": 4.2, "ticket": "免费"},
    {"name": "朱家角古镇", "province": "上海", "city": "上海", "category": "历史文化",
     "description": "上海保存最完好的江南水乡古镇，九条老街依水而建，被称为\"上海威尼斯\"。", "highlights": "放生桥、课植园、北大街、圆津禅院",
     "best_season": "3-5月、9-11月", "tips": "可以乘坐乌篷船游河。", "rating": 4.3, "ticket": "免费（景点联票60元）"},
    {"name": "上海科技馆", "province": "上海", "city": "上海", "category": "主题乐园",
     "description": "中国最大的科技博物馆之一，互动性极强，适合亲子游和科普学习。", "highlights": "动物世界、机器人世界、太空影院",
     "best_season": "四季皆宜", "tips": "带孩子的建议留出一整天。", "rating": 4.5, "ticket": "45元"},

    # ===== 天津 =====
    {"name": "天津之眼摩天轮", "province": "天津", "city": "天津", "category": "都市风情",
     "description": "世界上唯一建在桥上的摩天轮，直径110米，最高点可俯瞰天津全城夜景。", "highlights": "海河夜景、全景观光、浪漫体验",
     "best_season": "四季皆宜", "tips": "晚上乘坐效果最佳，建议提前购票。", "rating": 4.5, "ticket": "70元"},
    {"name": "五大道文化旅游区", "province": "天津", "city": "天津", "category": "历史文化",
     "description": "天津最具特色的历史风貌区，拥有英、法、意、德、西班牙等多种风格的小洋楼建筑群。", "highlights": "民园广场、瓷房子、庆王府、疙瘩楼",
     "best_season": "春秋两季", "tips": "建议骑共享单车游览，可参观马车体验。", "rating": 4.6, "ticket": "免费"},
    {"name": "意式风情区", "province": "天津", "city": "天津", "category": "都市风情",
     "description": "亚洲唯一的意大利风格建筑群，原为意大利租界，浓郁的欧洲风情。", "highlights": "马可波罗广场、但丁广场、意大利风情街",
     "best_season": "四季皆宜", "tips": "适合拍照打卡，晚上酒吧热闹。", "rating": 4.3, "ticket": "免费"},
    {"name": "盘山", "province": "天津", "city": "天津", "category": "自然风光",
     "description": "京东第一山，乾隆皇帝曾32次巡游此地，留下'早知有盘山，何必下江南'的赞叹。", "highlights": "挂月峰、万松寺、云罩寺、天成寺",
     "best_season": "4-10月", "tips": "可乘缆车上山，徒步下山欣赏沿途风景。", "rating": 4.4, "ticket": "78元"},
    {"name": "古文化街", "province": "天津", "city": "天津", "category": "历史文化",
     "description": "天津老字号聚集地，汇集了泥人张、杨柳青年画等天津传统工艺。", "highlights": "天后宫、泥人张、杨柳青年画、十八街麻花",
     "best_season": "四季皆宜", "tips": "可以品尝天津特色小吃。", "rating": 4.3, "ticket": "免费"},

    # ===== 重庆（补充） =====
    {"name": "长江索道", "province": "重庆", "city": "重庆", "category": "都市风情",
     "description": "横跨长江的空中索道，被誉为\"万里长江第一条空中走廊\"，是观赏重庆山水之景的独特方式。", "highlights": "空中观江、两岸夜景、山城风光",
     "best_season": "四季皆宜", "tips": "建议傍晚乘坐，欣赏日落和夜景。", "rating": 4.4, "ticket": "单程20元"},
    {"name": "武隆天生三桥", "province": "重庆", "city": "重庆", "category": "自然风光",
     "description": "世界自然遗产，拥有三座天然石拱桥和天坑、地缝等喀斯特地貌奇观。", "highlights": "天龙桥、青龙桥、黑龙桥、天福驿",
     "best_season": "4-10月", "tips": "景区较大建议留出4-5小时。", "rating": 4.7, "ticket": "135元"},
    {"name": "磁器口古镇", "province": "重庆", "city": "重庆", "category": "历史文化",
     "description": "重庆最具代表性的古镇之一，千年历史的码头古镇，如今是美食和文艺小店聚集地。", "highlights": "陈麻花、古镇鸡杂、宝轮寺、码头文化",
     "best_season": "四季皆宜", "tips": "周末人特别多，建议周中前往。", "rating": 4.3, "ticket": "免费"},
    {"name": "南山一棵树观景台", "province": "重庆", "city": "重庆", "category": "自然风光",
     "description": "观赏重庆夜景的最佳地点之一，可俯瞰渝中半岛和长江、嘉陵江交汇的壮观景色。", "highlights": "重庆全景、夜景摄影、渝中半岛",
     "best_season": "四季皆宜", "tips": "日落前前往，看白天→黄昏→夜景三个时段。", "rating": 4.5, "ticket": "30元"},
    {"name": "大足石刻", "province": "重庆", "city": "重庆", "category": "历史文化",
     "description": "世界文化遗产，是唐宋时期石窟艺术的巅峰之作，以宝顶山和北山摩崖造像最为著名。", "highlights": "千手观音、卧佛、六道轮回图、华严三圣",
     "best_season": "春秋两季", "tips": "建议请导游讲解佛教文化背景。", "rating": 4.8, "ticket": "135元"},

    # ===== 河北（补充） =====
    {"name": "北戴河", "province": "河北", "city": "秦皇岛", "category": "自然风光",
     "description": "中国著名的海滨避暑胜地，拥有优质海滩和清新的空气，是京津地区最受欢迎的海滨度假地。", "highlights": "鸽子窝公园、老虎石海滩、联峰山、观鸟",
     "best_season": "5-9月", "tips": "暑期是旺季，建议提前预订住宿。", "rating": 4.3, "ticket": "免费（部分景点收费）"},
    {"name": "野三坡", "province": "河北", "city": "保定", "category": "自然风光",
     "description": "国家级风景名胜区，以雄、险、奇、幽的自然景观闻名，百里峡谷景色壮美。", "highlights": "百里峡、鱼谷洞、龙门天关、白草畔",
     "best_season": "5-10月", "tips": "百里峡是最精华部分，建议徒步游览。", "rating": 4.4, "ticket": "100元"},
    {"name": "清西陵", "province": "河北", "city": "保定", "category": "历史文化",
     "description": "清朝最后一处帝王陵墓建筑群，葬有雍正、嘉庆、道光、光绪四位皇帝。", "highlights": "泰陵、昌陵、慕陵、崇陵",
     "best_season": "春秋两季", "tips": "与清东陵齐名，但游客较少更清静。", "rating": 4.2, "ticket": "120元"},

    # ===== 黑龙江 =====
    {"name": "冰雪大世界", "province": "黑龙江", "city": "哈尔滨", "category": "主题乐园",
     "description": "世界最大的冰雪主题乐园，每年冬季在哈尔滨举行，展出巨型冰雕、雪雕和冰雪建筑。", "highlights": "冰雕展览、冰雪滑梯、冰雪演艺、灯光秀",
     "best_season": "12-2月", "tips": "注意保暖，温度可达-30℃，建议穿最厚的羽绒服。", "rating": 4.7, "ticket": "330元"},
    {"name": "太阳岛风景区", "province": "黑龙江", "city": "哈尔滨", "category": "自然风光",
     "description": "哈尔滨的城市绿肺，冬季是雪博会举办地，夏季是避暑胜地。", "highlights": "太阳瀑、松鼠岛、雪博会、俄罗斯风情小镇",
     "best_season": "四季皆宜（夏季避暑，冬季看雪）", "tips": "建议租自行车游览，岛上很大。", "rating": 4.3, "ticket": "30元"},
    {"name": "圣索菲亚大教堂", "province": "黑龙江", "city": "哈尔滨", "category": "历史文化",
     "description": "远东地区最大的东正教教堂，拜占庭式建筑风格，是哈尔滨的标志性建筑。", "highlights": "建筑外观、内部壁画、建筑艺术馆",
     "best_season": "四季皆宜", "tips": "夜景格外美丽，广场上喂鸽子很有氛围。", "rating": 4.5, "ticket": "20元"},
    {"name": "五大连池", "province": "黑龙江", "city": "黑河", "category": "自然风光",
     "description": "世界地质公园，拥有独特的火山地貌和矿泉资源，被称为\"天然火山博物馆\"。", "highlights": "老黑山、火烧山、药泉山、温泊",
     "best_season": "5-9月", "tips": "可以品尝当地的矿泉水和矿泉鱼。", "rating": 4.5, "ticket": "180元"},
    {"name": "扎龙自然保护区", "province": "黑龙江", "city": "齐齐哈尔", "category": "自然风光",
     "description": "世界最大的丹顶鹤繁殖基地，中国著名湿地保护区，每年吸引大量摄影爱好者。", "highlights": "丹顶鹤放飞、湿地观鸟、芦苇荡",
     "best_season": "4-10月", "tips": "丹顶鹤放飞一般在上午9点和下午2点。", "rating": 4.4, "ticket": "65元"},

    # ===== 吉林 =====
    {"name": "长白山天池", "province": "吉林", "city": "延边", "category": "自然风光",
     "description": "中国最深的湖泊，中朝界湖，位于长白山主峰火山口，湖水湛蓝如宝石般璀璨。", "highlights": "天池、长白瀑布、地下森林、绿渊潭",
     "best_season": "7-9月", "tips": "天池天气多变，能否看到全貌靠运气。", "rating": 4.8, "ticket": "105元"},
    {"name": "净月潭", "province": "吉林", "city": "长春", "category": "自然风光",
     "description": "国家森林公园，有\"亚洲第一大人工林海\"之称，四季景色各异。", "highlights": "森林浴场、滑雪场、北普陀寺、荷花垂柳园",
     "best_season": "四季皆宜", "tips": "冬季可滑雪，夏季可划船。", "rating": 4.3, "ticket": "30元"},
    {"name": "伪满皇宫博物院", "province": "吉林", "city": "长春", "category": "历史文化",
     "description": "清朝末代皇帝溥仪充当伪满洲国傀儡皇帝时的宫廷旧址，见证了那段屈辱历史。", "highlights": "缉熙楼、勤民楼、同德殿、防空洞",
     "best_season": "四季皆宜", "tips": "建议参观2-3小时，了解东北近代史。", "rating": 4.4, "ticket": "70元"},
    {"name": "雾凇岛", "province": "吉林", "city": "吉林", "category": "自然风光",
     "description": "中国四大自然奇观之一，冬季松花江畔的雾凇景观如梦如幻，摄影师的天堂。", "highlights": "雾凇奇观、日出摄影、冰雪体验",
     "best_season": "12-2月", "tips": "冬季清晨6-8点是观赏雾凇的最佳时间。", "rating": 4.6, "ticket": "80元"},

    # ===== 贵州 =====
    {"name": "黄果树瀑布", "province": "贵州", "city": "安顺", "category": "自然风光",
     "description": "亚洲最大的瀑布，高77.8米、宽101米，以水势浩大著称，是贵州最著名的自然景观。", "highlights": "黄果树大瀑布、水帘洞、陡坡塘瀑布、天星桥",
     "best_season": "6-10月（雨季水量大）", "tips": "夏季水量最大但也是旺季，建议穿雨衣进水帘洞。", "rating": 4.7, "ticket": "160元"},
    {"name": "荔波小七孔", "province": "贵州", "city": "黔南", "category": "自然风光",
     "description": "世界自然遗产，以喀斯特森林、湖泊、瀑布、溶洞著称，被称为\"地球腰带上的绿宝石\"。", "highlights": "小七孔桥、拉雅瀑布、水上森林、卧龙潭",
     "best_season": "4-10月", "tips": "建议从东门进西门出，一路下坡省力。", "rating": 4.7, "ticket": "130元"},
    {"name": "西江千户苗寨", "province": "贵州", "city": "黔东南", "category": "历史文化",
     "description": "世界上最大的苗族聚居村寨，层层叠叠的吊脚楼依山而建，夜景尤为壮观。", "highlights": "吊脚楼群、苗族歌舞、长桌宴、观景台夜景",
     "best_season": "5-10月", "tips": "一定要住一晚看夜景和晨景。", "rating": 4.4, "ticket": "90元"},
    {"name": "梵净山", "province": "贵州", "city": "铜仁", "category": "自然风光",
     "description": "世界自然遗产，佛教名山，以红云金顶、蘑菇石等奇特的喀斯特地貌闻名。", "highlights": "红云金顶、蘑菇石、万步云梯、承恩寺",
     "best_season": "4-6月、9-11月", "tips": "登山较累，建议乘坐索道上下。", "rating": 4.6, "ticket": "100元"},

    # ===== 山西（补充） =====
    {"name": "悬空寺", "province": "山西", "city": "大同", "category": "历史文化",
     "description": "建于北魏时期，悬挂在恒山金龙峡翠屏峰的悬崖峭壁上，是中国仅存的佛、道、儒三教合一的寺庙。", "highlights": "悬空建筑、三教殿、栈道、远眺恒山",
     "best_season": "春秋两季", "tips": "恐高者慎重，登寺需要走狭窄楼梯。", "rating": 4.6, "ticket": "115元"},
    {"name": "王家大院", "province": "山西", "city": "晋中", "category": "历史文化",
     "description": "清代民居建筑的集大成者，比故宫还大的民间豪宅，有\"王家归来不看院\"的美誉。", "highlights": "高家崖、红门堡、司马第、古建筑雕刻",
     "best_season": "春夏秋三季", "tips": "至少留出3-4小时，院子非常大。", "rating": 4.6, "ticket": "55元"},
    {"name": "壶口瀑布", "province": "山西", "city": "临汾", "category": "自然风光",
     "description": "黄河上最大的瀑布，气势磅礴，瀑布水雾在阳光下形成彩虹，极为壮观。", "highlights": "黄河瀑布、彩虹奇观、龙洞观瀑",
     "best_season": "5-10月", "tips": "春秋两季水量适中，观赏效果最佳。", "rating": 4.6, "ticket": "100元"},
    {"name": "晋祠", "province": "山西", "city": "太原", "category": "历史文化",
     "description": "中国现存最早的古典祠堂建筑群，为纪念晋国诸侯而建，是山西最古老的文化遗产之一。", "highlights": "圣母殿、鱼沼飞梁、难老泉、周柏",
     "best_season": "春夏秋三季", "tips": "建议请导游讲解历史故事。", "rating": 4.5, "ticket": "80元"},

    # ===== 新疆（补充） =====
    {"name": "喀纳斯湖", "province": "新疆", "city": "阿勒泰", "category": "自然风光",
     "description": "新疆最著名的高山湖泊，湖水随季节变换颜色，秋季层林尽染美不胜收，传说中的湖怪更是增添了神秘色彩。", "highlights": "观鱼台、月亮湾、神仙湾、三湾徒步",
     "best_season": "9-10月（秋季最美）", "tips": "秋季是旺季，需提前预订住宿和交通。", "rating": 4.8, "ticket": "230元"},
    {"name": "赛里木湖", "province": "新疆", "city": "博尔塔拉", "category": "自然风光",
     "description": "大西洋最后一滴眼泪，新疆海拔最高、面积最大的高山冷水湖，湖水蓝得令人心醉。", "highlights": "环湖公路、天鹅乐园、西海草原、点将台",
     "best_season": "6-8月", "tips": "环湖一圈约90公里，建议自驾或包车。", "rating": 4.8, "ticket": "70元"},
    {"name": "天山天池", "province": "新疆", "city": "昌吉", "category": "自然风光",
     "description": "古称瑶池，传说中西王母居住的地方，天山博格达峰脚下的高山冰碛湖。", "highlights": "天池湖景、马牙山、西王母庙、博格达峰",
     "best_season": "6-9月", "tips": "山上较冷，建议带外套。", "rating": 4.5, "ticket": "155元"},
    {"name": "国际大巴扎", "province": "新疆", "city": "乌鲁木齐", "category": "都市风情",
     "description": "世界规模最大的巴扎（集市），浓郁的维吾尔族风情，是体验新疆民族文化的最佳场所。", "highlights": "民族工艺品、干果市场、歌舞表演、清真寺",
     "best_season": "四季皆宜", "tips": "可以购买干果和手工艺品，记得砍价。", "rating": 4.3, "ticket": "免费"},
    {"name": "火焰山", "province": "新疆", "city": "吐鲁番", "category": "自然风光",
     "description": "《西游记》中描写的火焰山原型，夏季地表温度可达70℃以上，红色山体在烈日下似火焰燃烧。", "highlights": "火焰山景区、葡萄沟、坎儿井、千佛洞",
     "best_season": "春季或秋季", "tips": "夏季极热，建议早上或傍晚前往。", "rating": 4.2, "ticket": "40元"},

    # ===== 内蒙古（补充） =====
    {"name": "呼伦贝尔草原", "province": "内蒙古", "city": "呼伦贝尔", "category": "自然风光",
     "description": "中国最美的草原之一，天苍苍野茫茫，风吹草低见牛羊的壮阔景象尽收眼底。", "highlights": "莫日格勒河、额尔古纳湿地、蒙古包体验、那达慕",
     "best_season": "6-8月", "tips": "夏季蚊虫多，备好驱蚊用品；昼夜温差大。", "rating": 4.8, "ticket": "免费"},
    {"name": "成吉思汗陵", "province": "内蒙古", "city": "鄂尔多斯", "category": "历史文化",
     "description": "一代天骄成吉思汗的衣冠冢，蒙古族人民心中的圣地，建筑宏伟具有浓郁的民族特色。", "highlights": "成吉思汗雕像、陵宫建筑、蒙古历史文化展",
     "best_season": "6-9月", "tips": "每年农历三月二十一的祭典最为隆重。", "rating": 4.4, "ticket": "80元"},
    {"name": "阿尔山国家森林公园", "province": "内蒙古", "city": "兴安盟", "category": "自然风光",
     "description": "大兴安岭腹地的火山熔岩地貌，天池、温泉、森林、河流交织成一幅天然画卷。", "highlights": "阿尔山天池、杜鹃湖、石塘林、驼峰岭天池",
     "best_season": "6-9月", "tips": "秋季9月中旬层林尽染是最美季节。", "rating": 4.6, "ticket": "180元"},

    # ===== 辽宁（补充） =====
    {"name": "大连老虎滩海洋公园", "province": "辽宁", "city": "大连", "category": "主题乐园",
     "description": "中国最大的现代化海滨游乐场之一，集海洋动物表演、极地馆、珊瑚馆于一体。", "highlights": "极地馆、海豚表演、珊瑚馆、鸟语林",
     "best_season": "5-10月", "tips": "建议上午入馆看表演，下午逛其他场馆。", "rating": 4.5, "ticket": "220元"},
    {"name": "沈阳故宫", "province": "辽宁", "city": "沈阳", "category": "历史文化",
     "description": "清朝入关前的皇宫，是北京故宫之外的又一皇家宫殿建筑群，见证了大清的崛起。", "highlights": "大政殿、凤凰楼、文溯阁、崇政殿",
     "best_season": "春秋两季", "tips": "比北京故宫小很多，2-3小时即可游览完毕。", "rating": 4.5, "ticket": "60元"},
    {"name": "千山", "province": "辽宁", "city": "鞍山", "category": "自然风光",
     "description": "辽东第一山，以奇峰、怪石、古庙、梨花著称，有\"东北明珠\"的美誉。", "highlights": "仙人台、五佛顶、大佛寺、天上天",
     "best_season": "4-10月", "tips": "登山约需半天，备好登山鞋。", "rating": 4.4, "ticket": "80元"},

    # ===== 甘肃（补充） =====
    {"name": "莫高窟", "province": "甘肃", "city": "敦煌", "category": "历史文化",
     "description": "世界文化遗产，世界上现存规模最大、内容最丰富的佛教艺术圣地，壁画和彩塑艺术冠绝天下。", "highlights": "第96窟、藏经洞、飞天壁画、九层楼",
     "best_season": "5-10月", "tips": "门票需提前预约，洞窟内禁止拍照。", "rating": 4.9, "ticket": "238元"},
    {"name": "张掖丹霞地质公园", "province": "甘肃", "city": "张掖", "category": "自然风光",
     "description": "中国最美的丹霞地貌之一，七彩的山脉如同大地的调色盘，日出日落时分最为壮观。", "highlights": "七彩丹霞、冰沟丹霞、日落观景台",
     "best_season": "6-9月", "tips": "日落前2小时到达，光线最美。", "rating": 4.7, "ticket": "74元"},
    {"name": "鸣沙山月牙泉", "province": "甘肃", "city": "敦煌", "category": "自然风光",
     "description": "沙漠中的奇观——鸣沙山环绕着一弯形似月牙的泉水，千年不涸，令人称奇。", "highlights": "骑骆驼、滑沙、月牙泉、沙漠日落",
     "best_season": "5-10月", "tips": "建议傍晚去，可以看沙漠日落。", "rating": 4.6, "ticket": "120元"},
    {"name": "嘉峪关", "province": "甘肃", "city": "嘉峪关", "category": "历史文化",
     "description": "明长城西端起点，天下第一雄关，古代丝绸之路的重要关隘。", "highlights": "城楼、长城博物馆、悬壁长城、长城第一墩",
     "best_season": "5-10月", "tips": "关城很大，建议游览2-3小时。", "rating": 4.5, "ticket": "110元"},

    # ===== 福建（补充） =====
    {"name": "武夷山", "province": "福建", "city": "南平", "category": "自然风光",
     "description": "世界文化与自然双重遗产，以丹霞地貌、九曲溪竹筏漂流和武夷岩茶闻名于世。", "highlights": "九曲溪竹筏、天游峰、大红袍母树、武夷宫",
     "best_season": "5-11月", "tips": "竹筏漂流是最经典项目，建议提前购票。", "rating": 4.7, "ticket": "140元"},
    {"name": "土楼（福建土楼）", "province": "福建", "city": "龙岩", "category": "历史文化",
     "description": "世界文化遗产，客家先民建造的独特大型夯土民居建筑，圆形方形的土楼群壮观而神秘。", "highlights": "承启楼、振成楼、田螺坑土楼群、云水谣",
     "best_season": "3-5月、9-11月", "tips": "建议住一晚土楼民宿，体验客家生活。", "rating": 4.6, "ticket": "90元"},
    {"name": "太姥山", "province": "福建", "city": "宁德", "category": "自然风光",
     "description": "海上仙都，以花岗岩峰林、幽洞、云雾闻名，山海相依的独特景观。", "highlights": "一线天、九鲤湖、白云寺、夫妻峰",
     "best_season": "4-11月", "tips": "洞道狭窄，注意安全。", "rating": 4.4, "ticket": "100元"},

    # ===== 湖南（补充） =====
    {"name": "张家界武陵源", "province": "湖南", "city": "张家界", "category": "自然风光",
     "description": "世界自然遗产，三千多座石英砂岩柱峰拔地而起，电影《阿凡达》悬浮山的灵感来源。", "highlights": "袁家界、天子山、金鞭溪、十里画廊",
     "best_season": "4-6月、9-11月", "tips": "建议游玩2-3天，山上住宿需提前预订。", "rating": 4.8, "ticket": "225元"},
    {"name": "凤凰古城", "province": "湖南", "city": "湘西", "category": "历史文化",
     "description": "沈从文笔下的边城，沱江两岸的吊脚楼诉说着湘西的千年故事，是中国最美的小城之一。", "highlights": "沱江泛舟、古城墙、虹桥、沈从文故居",
     "best_season": "3-11月", "tips": "清晨和夜晚的古城最有韵味。", "rating": 4.4, "ticket": "免费"},
    {"name": "岳麓山", "province": "湖南", "city": "长沙", "category": "历史文化",
     "description": "湖湘文化重地，岳麓书院是中国四大书院之一，爱晚亭因杜牧诗句而闻名。", "highlights": "岳麓书院、爱晚亭、橘子洲、云麓宫",
     "best_season": "春秋两季", "tips": "秋天层林尽染最美，可乘索道上山。", "rating": 4.5, "ticket": "免费"},
    {"name": "韶山", "province": "湖南", "city": "湘潭", "category": "历史文化",
     "description": "毛泽东的故乡，中国重要的红色旅游目的地，每年吸引大量游客前来瞻仰。", "highlights": "毛泽东故居、铜像广场、滴水洞、韶峰",
     "best_season": "四季皆宜", "tips": "景区免费但需身份证领票。", "rating": 4.3, "ticket": "免费"},

    # ===== 湖北（补充） =====
    {"name": "黄鹤楼", "province": "湖北", "city": "武汉", "category": "历史文化",
     "description": "天下江山第一楼，江南三大名楼之一，因崔颢'昔人已乘黄鹤去'诗句而千古流传。", "highlights": "黄鹤楼、白云阁、千禧钟、诗词碑廊",
     "best_season": "春秋两季", "tips": "登楼可俯瞰长江和武汉三镇。", "rating": 4.5, "ticket": "70元"},
    {"name": "武当山", "province": "湖北", "city": "十堰", "category": "历史文化",
     "description": "道教圣地，太极武术的发源地，古建筑群被列为世界文化遗产。", "highlights": "金顶、紫霄宫、南岩宫、太子坡、太极表演",
     "best_season": "4-10月", "tips": "山很大，建议游玩2天，山上住宿。", "rating": 4.7, "ticket": "243元"},
    {"name": "东湖风景区", "province": "湖北", "city": "武汉", "category": "自然风光",
     "description": "中国最大的城中湖，面积是杭州西湖的6倍，拥有优美的湖光山色。", "highlights": "听涛景区、磨山景区、落雁岛、东湖绿道",
     "best_season": "3-5月、9-11月", "tips": "东湖绿道很适合骑行，可租共享单车。", "rating": 4.5, "ticket": "免费"},
    {"name": "神农架", "province": "湖北", "city": "神农架林区", "category": "自然风光",
     "description": "世界自然遗产，华中屋脊，神秘的野人传说让这片原始森林更加引人入胜。", "highlights": "神农顶、大九湖、天生桥、神农坛",
     "best_season": "5-10月", "tips": "山区天气多变，带好雨具和保暖衣物。", "rating": 4.6, "ticket": "269元"},

    # ===== 广东（补充） =====
    {"name": "广州塔", "province": "广东", "city": "广州", "category": "现代建筑",
     "description": "广州地标建筑，高600米，是中国第一高塔，塔顶摩天轮和跳楼机带来独特体验。", "highlights": "观景台、摩天轮、极速云霄、433米白云星空",
     "best_season": "四季皆宜", "tips": "建议傍晚登塔，欣赏珠江夜景。", "rating": 4.5, "ticket": "150元"},
    {"name": "长隆野生动物世界", "province": "广东", "city": "广州", "category": "主题乐园",
     "description": "亚洲最大的野生动物主题公园，拥有全球唯一的大熊猫三胞胎，可以自驾游览。", "highlights": "熊猫乐园、自驾区、缆车观光、白虎表演",
     "best_season": "四季皆宜", "tips": "建议一开门就入园，先坐小火车游览自驾区。", "rating": 4.7, "ticket": "300元"},
    {"name": "世界之窗", "province": "广东", "city": "深圳", "category": "主题乐园",
     "description": "中国最著名的微缩景观主题公园，汇集了世界各地的标志性建筑缩小版。", "highlights": "埃菲尔铁塔、金字塔、尼亚加拉瀑布、日本园",
     "best_season": "四季皆宜", "tips": "晚上有精彩的表演和灯光秀。", "rating": 4.3, "ticket": "220元"},
    {"name": "开平碉楼", "province": "广东", "city": "江门", "category": "历史文化",
     "description": "世界文化遗产，中西合璧的碉楼建筑群，电影《让子弹飞》的取景地。", "highlights": "自力村碉楼群、马降龙碉楼群、立园",
     "best_season": "3-5月、9-11月", "tips": "自力村是最精华的部分，建议请导游。", "rating": 4.4, "ticket": "78元"},

    # ===== 浙江（补充） =====
    {"name": "千岛湖", "province": "浙江", "city": "杭州", "category": "自然风光",
     "description": "拥有1078个岛屿的人工湖，以湖光山色和纯净水质闻名，是长三角的度假胜地。", "highlights": "梅峰岛、龙山岛、月光岛、环湖骑行",
     "best_season": "4-6月、9-11月", "tips": "建议住一晚，乘船游览各岛。", "rating": 4.6, "ticket": "185元"},
    {"name": "乌镇", "province": "浙江", "city": "嘉兴", "category": "历史文化",
     "description": "中国最美的水乡古镇之一，完整保存了江南水乡的格局和风貌，分东栅和西栅两大景区。", "highlights": "西栅夜景、东栅老街、木心美术馆、茅盾故居",
     "best_season": "3-5月、9-11月", "tips": "西栅的夜景非常美，建议住一晚。", "rating": 4.5, "ticket": "西栅150元，东栅120元"},
    {"name": "雁荡山", "province": "浙江", "city": "温州", "category": "自然风光",
     "description": "中国十大名山之一，以奇峰、怪石、飞瀑、幽洞著称，有\"海上名山\"之称。", "highlights": "灵峰、大龙湫、灵岩、方洞",
     "best_season": "4-11月", "tips": "灵峰夜景是一绝，不同角度看山形变化。", "rating": 4.5, "ticket": "各景区分别售票约50元"},
    {"name": "普陀山", "province": "浙江", "city": "舟山", "category": "历史文化",
     "description": "中国四大佛教名山之一，观音菩萨的道场，海岛佛教圣地兼具山海之胜。", "highlights": "南海观音、普济寺、法雨寺、佛顶山",
     "best_season": "3-5月、9-11月", "tips": "上岛需乘船，建议避开法定节假日。", "rating": 4.6, "ticket": "160元（含船票）"},

    # ===== 陕西（补充） =====
    {"name": "华山", "province": "陕西", "city": "渭南", "category": "自然风光",
     "description": "五岳之中以险著称的西岳，长空栈道和鹞子翻身是勇敢者的挑战。", "highlights": "长空栈道、鹞子翻身、东峰观日、西峰索道",
     "best_season": "4-10月", "tips": "夜爬华山看日出是经典路线，备好手套和头灯。", "rating": 4.7, "ticket": "160元"},
    {"name": "大雁塔", "province": "陕西", "city": "西安", "category": "历史文化",
     "description": "唐代高僧玄奘为保存佛经而建，是西安的标志性建筑，位于大慈恩寺内。", "highlights": "大雁塔、大慈恩寺、北广场音乐喷泉、大唐不夜城",
     "best_season": "四季皆宜", "tips": "晚上大唐不夜城灯光秀很精彩。", "rating": 4.5, "ticket": "25元"},
    {"name": "陕西历史博物馆", "province": "陕西", "city": "西安", "category": "历史文化",
     "description": "中国最重要的历史博物馆之一，馆藏文物171万件，周、秦、汉、唐文物尤为丰富。", "highlights": "商周青铜器、秦汉陶俑、唐代金银器、壁画",
     "best_season": "四季皆宜", "tips": "免费开放但需提前预约，一票难求。", "rating": 4.8, "ticket": "免费（珍宝馆30元）"},
    {"name": "法门寺", "province": "陕西", "city": "宝鸡", "category": "历史文化",
     "description": "世界唯一的佛指舍利供奉地，唐代皇家寺院，出土了大量珍贵的唐代文物。", "highlights": "合十舍利塔、地宫文物、佛指舍利、法门寺博物馆",
     "best_season": "四季皆宜", "tips": "舍利瞻拜有固定时间，提前查询。", "rating": 4.5, "ticket": "120元"},

    # ===== 江苏（补充） =====
    {"name": "周庄", "province": "江苏", "city": "苏州", "category": "历史文化",
     "description": "中国第一水乡，900多年的历史，小桥流水人家的江南水乡典范。", "highlights": "双桥、沈厅、张厅、富安桥、南湖秋月",
     "best_season": "3-5月、9-11月", "tips": "清晨和傍晚的周庄最美，建议住一晚。", "rating": 4.4, "ticket": "100元"},
    {"name": "拙政园", "province": "江苏", "city": "苏州", "category": "历史文化",
     "description": "中国四大名园之一，苏州园林的杰出代表，以精巧的布局和借景手法著称。", "highlights": "远香堂、小飞虹、见山楼、荷风四面亭",
     "best_season": "四季皆宜", "tips": "四季景色各异，建议早晨开园时前往。", "rating": 4.7, "ticket": "80元"},
    {"name": "中山陵", "province": "江苏", "city": "南京", "category": "历史文化",
     "description": "孙中山先生的陵墓，位于紫金山南麓，392级台阶象征当年中国3亿9千2百万人口。", "highlights": "祭堂、392级台阶、音乐台、紫金山观景",
     "best_season": "3-5月、9-11月", "tips": "景区免费，需提前预约。", "rating": 4.6, "ticket": "免费"},

    # ===== 安徽（补充） =====
    {"name": "宏村", "province": "安徽", "city": "黄山", "category": "历史文化",
     "description": "世界文化遗产，中国画里乡村，牛形布局的水系和徽派建筑完美结合。", "highlights": "月沼、南湖、承志堂、汪氏宗祠",
     "best_season": "3-5月、9-11月", "tips": "清晨的月沼倒影是最经典的拍照角度。", "rating": 4.6, "ticket": "104元"},
    {"name": "九华山", "province": "安徽", "city": "池州", "category": "历史文化",
     "description": "中国四大佛教名山之一，地藏王菩萨的道场，有\"莲花佛国\"之称。", "highlights": "肉身宝殿、天台峰、百岁宫、化城寺",
     "best_season": "3-5月、9-11月", "tips": "登山较累，可乘索道上山。", "rating": 4.6, "ticket": "160元"},
    {"name": "西递", "province": "安徽", "city": "黄山", "category": "历史文化",
     "description": "世界文化遗产，与宏村齐名的徽派古村落，以精美的徽派建筑和深厚的文化底蕴著称。", "highlights": "胡文光牌坊、追慕堂、西园、敬爱堂",
     "best_season": "3-5月、9-11月", "tips": "相比宏村更为宁静，适合慢慢逛。", "rating": 4.5, "ticket": "104元"},

    # ===== 河南（补充） =====
    {"name": "龙门石窟", "province": "河南", "city": "洛阳", "category": "历史文化",
     "description": "世界文化遗产，中国三大石窟之一，北魏至唐的皇家石窟造像艺术集大成者。", "highlights": "卢舍那大佛、宾阳三洞、万佛洞、香山寺",
     "best_season": "3-5月、9-11月", "tips": "建议下午去，西山石窟光线最好。", "rating": 4.8, "ticket": "90元"},
    {"name": "老君山", "province": "河南", "city": "洛阳", "category": "自然风光",
     "description": "道教始祖老子归隐修炼之地，云海和金顶道观群构成了一幅人间仙境。", "highlights": "金顶道观群、云海日出、马鬃岭、追梦谷",
     "best_season": "4-10月", "tips": "冬季雪后老君山更是绝美。", "rating": 4.7, "ticket": "100元"},
    {"name": "清明上河园", "province": "河南", "city": "开封", "category": "主题乐园",
     "description": "以张择端《清明上河图》为蓝本建造的大型宋代文化主题公园，沉浸式体验北宋风情。", "highlights": "东京梦华演出、虹桥、古装体验、市井表演",
     "best_season": "3-5月、9-11月", "tips": "大型实景演出《东京梦华》非常震撼。", "rating": 4.4, "ticket": "120元"},

    # ===== 山东（补充） =====
    {"name": "泰山", "province": "山东", "city": "泰安", "category": "自然风光",
     "description": "五岳独尊，世界文化与自然双重遗产，历代帝王封禅之地，登泰山而小天下。", "highlights": "玉皇顶、十八盘、南天门、岱庙、日出云海",
     "best_season": "5-11月", "tips": "夜爬泰山看日出是经典行程，全程约4-5小时。", "rating": 4.8, "ticket": "115元"},
    {"name": "曲阜三孔", "province": "山东", "city": "济宁", "category": "历史文化",
     "description": "孔庙、孔府、孔林，纪念孔子的人文圣地，儒家文化的发源地。", "highlights": "大成殿、杏坛、孔府后花园、孔林神道",
     "best_season": "3-5月、9-11月", "tips": "建议请导游讲解儒家文化。", "rating": 4.6, "ticket": "三孔联票140元"},
    {"name": "青岛栈桥", "province": "山东", "city": "青岛", "category": "都市风情",
     "description": "青岛的标志性建筑，从海岸延伸入海的回澜阁，是观赏海景和青岛城市风光的经典地点。", "highlights": "回澜阁、栈桥海滨、小青岛、海岸线散步",
     "best_season": "5-10月", "tips": "夏季人很多，建议清晨或傍晚前往。", "rating": 4.3, "ticket": "免费"},

    # ===== 江西（补充） =====
    {"name": "三清山", "province": "江西", "city": "上饶", "category": "自然风光",
     "description": "世界自然遗产，道教名山，以奇特的峰林、怪石和云海著称，被誉为\"西太平洋最美的花岗岩\"。", "highlights": "巨蟒出山、司春女神、阳光海岸、三清宫",
     "best_season": "4-6月、9-11月", "tips": "山上住宿条件有限，建议一日游当天上下。", "rating": 4.7, "ticket": "150元"},
    {"name": "景德镇古窑民俗博览区", "province": "江西", "city": "景德镇", "category": "历史文化",
     "description": "中国唯一以陶瓷文化为主题的5A景区，可以近距离观看瓷器制作全过程。", "highlights": "古窑作坊、陶瓷博物馆、手工制瓷体验、创意市集",
     "best_season": "四季皆宜", "tips": "可以亲手体验制陶，很有意义。", "rating": 4.4, "ticket": "95元"},
    {"name": "龙虎山", "province": "江西", "city": "鹰潭", "category": "自然风光",
     "description": "道教发源地之一，正一道祖庭，丹霞地貌与悬棺文化交相辉映。", "highlights": "泸溪河竹筏、天师府、悬棺表演、仙女岩",
     "best_season": "4-10月", "tips": "竹筏漂流和悬棺表演是必看项目。", "rating": 4.4, "ticket": "120元"},

    # ===== 广西（补充） =====
    {"name": "德天跨国瀑布", "province": "广西", "city": "崇左", "category": "自然风光",
     "description": "亚洲最大的跨国瀑布，与越南板约瀑布相连，气势磅礴，四季景色各异。", "highlights": "德天瀑布、中越界碑、跨境集市、山水画廊",
     "best_season": "5-10月", "tips": "可以乘竹筏近距离观赏瀑布。", "rating": 4.6, "ticket": "80元"},
    {"name": "北海银滩", "province": "广西", "city": "北海", "category": "自然风光",
     "description": "中国最美的海滩之一，沙质细腻洁白，有\"天下第一滩\"之称。", "highlights": "银滩浴场、侨港风情街、涠洲岛、海底世界",
     "best_season": "4-10月", "tips": "夏季游泳注意安全，建议傍晚去不晒。", "rating": 4.4, "ticket": "免费"},
    {"name": "独秀峰王城", "province": "广西", "city": "桂林", "category": "历史文化",
     "description": "桂林市中心的明代藩王府邸，独秀峰是桂林的城市地标，'桂林山水甲天下'名句出自此处。", "highlights": "独秀峰、靖江王府、贡院、月牙池",
     "best_season": "四季皆宜", "tips": "登独秀峰可俯瞰桂林全城。", "rating": 4.3, "ticket": "100元"},

    # ===== 云南（补充） =====
    {"name": "洱海", "province": "云南", "city": "大理", "category": "自然风光",
     "description": "大理的标志性景观，高原淡水湖，环湖骑行是最受欢迎的游览方式。", "highlights": "双廊古镇、喜洲古镇、小普陀、环海公路",
     "best_season": "3-10月", "tips": "建议租电动车环湖，全程约120公里。", "rating": 4.6, "ticket": "免费"},
    {"name": "崇圣寺三塔", "province": "云南", "city": "大理", "category": "历史文化",
     "description": "大理国的皇家寺院，三塔倒影在洱海中的画面是云南的标志性名片。", "highlights": "千寻塔、南北小塔、三塔倒影公园、崇圣寺",
     "best_season": "四季皆宜", "tips": "三塔倒影公园的拍摄角度最佳。", "rating": 4.5, "ticket": "75元"},
    {"name": "西双版纳热带植物园", "province": "云南", "city": "西双版纳", "category": "自然风光",
     "description": "中国面积最大、植物多样性最丰富的植物园，有\"植物王国\"之称。", "highlights": "热带雨林区、棕榈园、奇花异木园、王莲池",
     "best_season": "11-4月（旱季）", "tips": "园区很大，建议乘坐电瓶车游览。", "rating": 4.6, "ticket": "80元"},

    # ===== 海南（补充） =====
    {"name": "海棠湾", "province": "海南", "city": "三亚", "category": "自然风光",
     "description": "三亚最负盛名的海滨度假区，拥有世界级的海滩和高端度假酒店群，是奢华度假的首选。", "highlights": "蜈支洲岛、亚特兰蒂斯、免税店、后海渔村",
     "best_season": "10-4月", "tips": "冬季是旺季，气温25℃左右最舒适。", "rating": 4.5, "ticket": "免费"},
    {"name": "南山文化旅游区", "province": "海南", "city": "三亚", "category": "历史文化",
     "description": "以佛教文化为主题的大型文化旅游区，拥有108米高的南海观音圣像。", "highlights": "南海观音、南山寺、金玉观音、三十三观音堂",
     "best_season": "四季皆宜", "tips": "景区很大，建议乘坐观光车。", "rating": 4.5, "ticket": "129元"},
    {"name": "呀诺达雨林", "province": "海南", "city": "保亭", "category": "自然风光",
     "description": "海南最著名的热带雨林景区，可以体验峡谷溯溪和高空滑索，感受雨林的神奇。", "highlights": "踏瀑戏水、高空滑索、雨林徒步、兰花谷",
     "best_season": "四季皆宜", "tips": "穿防滑鞋，踏瀑活动会湿身。", "rating": 4.3, "ticket": "185元"},

    # ===== 西藏（补充） =====
    {"name": "大昭寺", "province": "西藏", "city": "拉萨", "category": "历史文化",
     "description": "藏传佛教的圣殿，供奉着释迦牟尼12岁等身像，是朝圣者心中的终极目的地。", "highlights": "释迦牟尼像、金顶、壁画、八廓街转经",
     "best_season": "6-9月", "tips": "进入大昭寺需脱帽、不可拍照。", "rating": 4.7, "ticket": "85元"},
    {"name": "布达拉宫", "province": "西藏", "city": "拉萨", "category": "历史文化",
     "description": "世界上海拔最高、最宏伟的宫殿，藏传佛教的圣殿，被誉为\"世界屋脊上的明珠\"。", "highlights": "红宫、白宫、灵塔殿、金顶群",
     "best_season": "6-9月", "tips": "门票需提前在官方平台预约，参观限时1小时。", "rating": 4.9, "ticket": "200元"},
    {"name": "纳木错", "province": "西藏", "city": "那曲", "category": "自然风光",
     "description": "世界上海拔最高的咸水湖，西藏三大圣湖之一，湖面如镜倒映着念青唐古拉山。", "highlights": "扎西半岛、圣象天门、念青唐古拉山、星空",
     "best_season": "6-9月", "tips": "海拔4700米，注意高原反应。", "rating": 4.8, "ticket": "120元"},
    {"name": "南迦巴瓦峰", "province": "西藏", "city": "林芝", "category": "自然风光",
     "description": "中国最美雪山，海拔7782米，巨大的三角形峰体终年积雪，云雾缭绕难得一见真容。", "highlights": "南迦巴瓦日出、雅鲁藏布大峡谷、索松村、桃花沟",
     "best_season": "3-4月、9-11月", "tips": "春季桃花盛开时雪山和桃花同框最震撼。", "rating": 4.8, "ticket": "免费"},

    # ===== 青海（补充） =====
    {"name": "青海湖", "province": "青海", "city": "海南州", "category": "自然风光",
     "description": "中国最大的内陆湖和咸水湖，夏季油菜花与碧蓝湖水相映成画，骑行环湖是最经典的旅行方式。", "highlights": "环湖骑行、茶卡盐湖、黑马河日出、鸟岛",
     "best_season": "6-8月", "tips": "7月油菜花开是最佳季节，环湖360公里。", "rating": 4.7, "ticket": "100元"},
    {"name": "可可西里", "province": "青海", "city": "玉树", "category": "自然风光",
     "description": "世界自然遗产，中国最大的无人区，藏羚羊的家园，原始荒野的震撼无法用语言形容。", "highlights": "藏羚羊、昆仑山口、索南达杰保护站、高原荒漠",
     "best_season": "6-9月", "tips": "进入可可西里需要办理相关手续，建议跟团。", "rating": 4.7, "ticket": "免费"},

    # ===== 宁夏（补充） =====
    {"name": "沙坡头", "province": "宁夏", "city": "中卫", "category": "自然风光",
     "description": "中国十大最好玩的地方之一，集沙漠、黄河、绿洲于一体，可以体验滑沙、黄河飞索等刺激项目。", "highlights": "滑沙、黄河飞索、羊皮筏子、沙漠星空",
     "best_season": "5-10月", "tips": "沙漠徒步注意防晒补水。", "rating": 4.5, "ticket": "80元"},
    {"name": "西夏王陵", "province": "宁夏", "city": "银川", "category": "历史文化",
     "description": "西夏王朝的皇家陵墓群，被称为\"东方金字塔\"，是了解神秘西夏历史的重要窗口。", "highlights": "3号陵（元昊陵）、西夏博物馆、双陵、陵区风光",
     "best_season": "5-10月", "tips": "建议参观博物馆后再游览陵区。", "rating": 4.3, "ticket": "75元"},
    {"name": "镇北堡西部影城", "province": "宁夏", "city": "银川", "category": "历史文化",
     "description": "中国著名的影视基地，《大话西游》《红高粱》等多部经典电影的取景地。", "highlights": "明城、清城、老银川街、电影场景还原",
     "best_season": "四季皆宜", "tips": "建议穿古装拍照，非常出片。", "rating": 4.3, "ticket": "100元"},

    # ===== 香港（补充） =====
    {"name": "维多利亚港", "province": "香港", "city": "香港", "category": "都市风情",
     "description": "世界三大天然良港之一，香港的标志性景观，夜色中的维港灯火璀璨令人陶醉。", "highlights": "幻彩咏香江、天星小轮、星光大道、太平山顶",
     "best_season": "四季皆宜", "tips": "晚上8点有幻彩咏香江灯光秀。", "rating": 4.7, "ticket": "免费"},
    {"name": "海洋公园", "province": "香港", "city": "香港", "category": "主题乐园",
     "description": "香港最大的海洋主题公园，集海洋动物展览、游乐设施和表演于一体。", "highlights": "海洋奇观、熊猫馆、过山车、海豚表演",
     "best_season": "四季皆宜", "tips": "建议工作日前往，避开周末。", "rating": 4.5, "ticket": "498港币"},

    # ===== 澳门（补充） =====
    {"name": "大三巴牌坊", "province": "澳门", "city": "澳门", "category": "历史文化",
     "description": "澳门的标志性建筑，圣保禄教堂的前壁遗迹，东西方艺术交融的巴洛克式建筑。", "highlights": "大三巴牌坊、大炮台、澳门博物馆、恋爱巷",
     "best_season": "四季皆宜", "tips": "附近有很多澳门特色小吃店。", "rating": 4.5, "ticket": "免费"},
    {"name": "威尼斯人度假村", "province": "澳门", "city": "澳门", "category": "主题乐园",
     "description": "澳门最大的综合度假村，以威尼斯水城为主题，有人造运河和贡多拉游船。", "highlights": "大运河购物中心、贡多拉体验、威尼斯人剧场",
     "best_season": "四季皆宜", "tips": "室内的运河和蓝天白云天幕十分逼真。", "rating": 4.5, "ticket": "免费"},

    # ===== 台湾（补充） =====
    {"name": "台北101", "province": "台湾", "city": "台北", "category": "现代建筑",
     "description": "台北地标性建筑，曾是世界最高摩天大楼，独特的竹节造型融合了中华传统文化元素。", "highlights": "观景台、阻尼器观景区、101购物中心、跨年烟花",
     "best_season": "四季皆宜", "tips": "傍晚登顶欣赏台北夜景最美。", "rating": 4.5, "ticket": "600台币"},
    {"name": "日月潭", "province": "台湾", "city": "南投", "category": "自然风光",
     "description": "台湾最著名的高山湖泊，北半湖形如日轮，南半湖形如弯月，湖光山色如诗如画。", "highlights": "游船环湖、玄光寺、伊达邵、文武庙",
     "best_season": "四季皆宜", "tips": "建议租自行车环湖骑行。", "rating": 4.6, "ticket": "免费"},
    {"name": "士林夜市", "province": "台湾", "city": "台北", "category": "都市风情",
     "description": "台湾最大、最知名的夜市，各类小吃琳琅满目，是感受台湾市井文化的最佳去处。", "highlights": "蚵仔煎、士林大香肠、豪大大鸡排、生炒花枝",
     "best_season": "四季皆宜", "tips": "下午5点后摊位陆续开张。", "rating": 4.3, "ticket": "免费"},

    # ===== 四川（补充自不必说） =====
    {"name": "稻城亚丁", "province": "四川", "city": "甘孜", "category": "自然风光",
     "description": "蓝色星球上的最后一片净土，三神山和牛奶海构成了一幅绝美的画卷，是徒步爱好者的天堂。", "highlights": "牛奶海、五色海、洛绒牛场、仙乃日、央迈勇",
     "best_season": "9-10月", "tips": "海拔4000米以上，注意高原反应和保暖。", "rating": 4.7, "ticket": "146元"},
    {"name": "三星堆博物馆", "province": "四川", "city": "德阳", "category": "历史文化",
     "description": "世界最神秘的古蜀文化遗址，出土了青铜面具、青铜神树等震惊世界的文物，颠覆了对中国古代文明的认知。", "highlights": "青铜大立人、青铜神树、黄金面具、纵目面具",
     "best_season": "四季皆宜", "tips": "强烈建议请讲解或租讲解器，提前预约门票。", "rating": 4.7, "ticket": "72元"},
    {"name": "宽窄巷子", "province": "四川", "city": "成都", "category": "都市风情",
     "description": "成都最具代表性的历史文化街区，由宽巷子、窄巷子和井巷子组成，展现了老成都的休闲生活。", "highlights": "宽巷子（老建筑）、窄巷子（文艺小店）、川剧变脸、成都小吃",
     "best_season": "四季皆宜", "tips": "建议上午去人少，适合拍照。", "rating": 4.4, "ticket": "免费"},
    {"name": "成都大熊猫繁育研究基地", "province": "四川", "city": "成都", "category": "主题乐园",
     "description": "全球最大的大熊猫人工繁育基地，可以看到从幼崽到成年的大熊猫，是成都必打卡的景点。", "highlights": "月亮产房、太阳产房、幼年熊猫园、熊猫科普馆",
     "best_season": "春秋两季", "tips": "建议早上开园就入园，上午熊猫最活跃。", "rating": 4.7, "ticket": "55元"},

    # ===== 此前较少的省份补全 =====
    # 甘肃、贵州、山西、内蒙古、新疆等已在前面补全
    # 补充更多现代建筑和都市风情分类
]

# ===== 第二批扩充：补齐偏少省份 + 更多城市/主题/建筑 =====

EXPANSIONS_2 = [
    # === 更多 都市风情 ===
    {"name": "北京王府井大街", "province": "北京", "city": "北京", "category": "都市风情",
     "description": "北京最著名的商业步行街，百年老字号与现代商场并存，是体验北京都市生活的窗口。", "highlights": "王府井百货、东安市场、老北京小吃街、天主教堂",
     "best_season": "四季皆宜", "tips": "晚上灯火辉煌，比白天更有氛围。", "rating": 4.2, "ticket": "免费"},
    {"name": "上海新天地", "province": "上海", "city": "上海", "category": "都市风情",
     "description": "上海石库门老建筑改造的高端商业区，中西合璧，时尚与怀旧并存。", "highlights": "石库门建筑群、时尚餐厅、艺术画廊、中共一大会址",
     "best_season": "四季皆宜", "tips": "适合下午茶和晚餐，氛围很好。", "rating": 4.4, "ticket": "免费"},
    {"name": "广州北京路步行街", "province": "广东", "city": "广州", "category": "都市风情",
     "description": "广州最古老的商业街之一，千年古道遗址就在脚下，集购物、美食、文化于一体。", "highlights": "千年古道遗址、广府美食、老字号商铺、大佛寺",
     "best_season": "四季皆宜", "tips": "大佛寺夜景非常壮观。", "rating": 4.3, "ticket": "免费"},
    {"name": "成都春熙路", "province": "四川", "city": "成都", "category": "都市风情",
     "description": "成都最繁华的商业街，时尚地标IFS和太古里就在这里，是成都的城市名片。", "highlights": "IFS熊猫雕塑、太古里、方所书店、中山广场",
     "best_season": "四季皆宜", "tips": "IFS楼顶的爬墙大熊猫是必打卡机位。", "rating": 4.4, "ticket": "免费"},
    {"name": "重庆解放碑", "province": "重庆", "city": "重庆", "category": "都市风情",
     "description": "重庆的地标和城市心脏，抗战胜利纪功碑屹立于此，周边是繁华的商业区。", "highlights": "解放碑、八一好吃街、洪崖洞夜景、WFC观景台",
     "best_season": "四季皆宜", "tips": "晚上最热闹，周边美食众多。", "rating": 4.3, "ticket": "免费"},
    {"name": "武汉江汉路步行街", "province": "湖北", "city": "武汉", "category": "都市风情",
     "description": "武汉最长的步行街，拥有大量民国建筑，有\"天下第一步行街\"之称。", "highlights": "江汉关大楼、民国建筑群、吉庆街夜市、水塔美食街",
     "best_season": "四季皆宜", "tips": "江汉关大楼是武汉的标志性建筑。", "rating": 4.2, "ticket": "免费"},
    {"name": "南京夫子庙秦淮河", "province": "江苏", "city": "南京", "category": "都市风情",
     "description": "南京最繁华的文旅街区，秦淮河畔灯火阑珊，夫子庙内书香四溢。", "highlights": "夫子庙、秦淮河画舫、江南贡院、乌衣巷",
     "best_season": "3-5月、9-11月", "tips": "夜游秦淮河是最经典体验。", "rating": 4.4, "ticket": "免费"},
    {"name": "长沙黄兴路步行街", "province": "湖南", "city": "长沙", "category": "都市风情",
     "description": "长沙最热闹的市中心商业街，美食云集，烟火气十足。", "highlights": "火宫殿、坡子街美食、IFS国金中心、太平老街",
     "best_season": "四季皆宜", "tips": "长沙夜生活丰富，凌晨都还很热闹。", "rating": 4.3, "ticket": "免费"},
    {"name": "西安回民街", "province": "陕西", "city": "西安", "category": "都市风情",
     "description": "西安最具烟火气的美食街，回族风情浓郁，各种西北小吃琳琅满目。", "highlights": "羊肉泡馍、肉夹馍、凉皮、biangbiang面、高家大院",
     "best_season": "四季皆宜", "tips": "晚上最热闹，小吃种类最多。", "rating": 4.3, "ticket": "免费"},
    {"name": "哈尔滨中央大街", "province": "黑龙江", "city": "哈尔滨", "category": "都市风情",
     "description": "亚洲最长、中国最早的步行街，俄式建筑林立，充满异域风情。", "highlights": "圣索菲亚教堂、马迭尔冰棍、华梅西餐厅、防洪纪念塔",
     "best_season": "四季皆宜（冬季有冰雪景观）", "tips": "冬天来一定要吃马迭尔冰棍！", "rating": 4.4, "ticket": "免费"},
    {"name": "青岛中山路", "province": "山东", "city": "青岛", "category": "都市风情",
     "description": "青岛最早的商业街，德式建筑与海景交相辉映，直通栈桥。", "highlights": "栈桥、天主教堂、德国风情街、劈柴院美食",
     "best_season": "5-10月", "tips": "从中山路一直走到底就是栈桥。", "rating": 4.2, "ticket": "免费"},
    {"name": "厦门中山路", "province": "福建", "city": "厦门", "category": "都市风情",
     "description": "厦门最老牌的商业街，骑楼建筑独具特色，直通大海。", "highlights": "骑楼建筑、鼓浪屿轮渡、八市海鲜市场、黄则和花生汤",
     "best_season": "四季皆宜", "tips": "八市是厦门最地道的海鲜市场。", "rating": 4.3, "ticket": "免费"},
    {"name": "昆明南屏步行街", "province": "云南", "city": "昆明", "category": "都市风情",
     "description": "昆明市中心最繁华的商业步行街，周边历史文化景点密集。", "highlights": "金马碧鸡坊、正义坊、景星街花鸟市场、祥云美食城",
     "best_season": "四季皆宜", "tips": "金马碧鸡坊夜景很漂亮。", "rating": 4.2, "ticket": "免费"},

    # === 更多 现代建筑 ===
    {"name": "中央电视台总部大楼", "province": "北京", "city": "北京", "category": "现代建筑",
     "description": "北京最前卫的建筑之一，造型独特的Z形钢结构大厦，被戏称为\"大裤衩\"。", "highlights": "建筑外观、CBD夜景、国贸商圈",
     "best_season": "四季皆宜", "tips": "最佳拍照点在国贸三期或京广大厦。", "rating": 4.2, "ticket": "免费（外观）"},
    {"name": "广州大剧院", "province": "广东", "city": "广州", "category": "现代建筑",
     "description": "扎哈·哈迪德设计的世界级歌剧院，双砾石造型极具未来感，是广州的文化地标。", "highlights": "建筑外观、歌剧演出、珠江新城夜景、花城广场",
     "best_season": "四季皆宜", "tips": "即使不看演出，建筑本身也值得参观。", "rating": 4.4, "ticket": "30元（参观）"},
    {"name": "深圳平安金融中心", "province": "广东", "city": "深圳", "category": "现代建筑",
     "description": "中国第二高楼，深圳第一高楼，高599米，116层的云端观景台可俯瞰深圳全景。", "highlights": "云际观景台、阻尼器观光、Free Sky高空体验",
     "best_season": "四季皆宜", "tips": "傍晚登顶，可以同时看日落和夜景。", "rating": 4.4, "ticket": "200元"},
    {"name": "国家大剧院", "province": "北京", "city": "北京", "category": "现代建筑",
     "description": "北京的地标性文化建筑，巨大的钛金属穹顶宛如湖上明珠，内部声学设计世界一流。", "highlights": "穹顶建筑、人工湖、歌剧院、音乐厅",
     "best_season": "四季皆宜", "tips": "建议提前购票看一场演出。", "rating": 4.5, "ticket": "30元（参观）"},
    {"name": "上海中心大厦", "province": "上海", "city": "上海", "category": "现代建筑",
     "description": "中国第一高楼，632米，螺旋上升的造型极具未来感，拥有世界最快电梯。", "highlights": "118层观光厅、上海之巅、阻尼器灯光秀",
     "best_season": "四季皆宜", "tips": "建议天气晴朗时登顶，视野更远。", "rating": 4.6, "ticket": "180元"},
    {"name": "成都金融城双子塔", "province": "四川", "city": "成都", "category": "现代建筑",
     "description": "成都的新地标，交子公园旁的摩天双塔，夜景灯光秀是成都的新名片。", "highlights": "双子塔灯光秀、交子公园、SKP商圈",
     "best_season": "四季皆宜", "tips": "晚上灯光秀时间是最大看点。", "rating": 4.3, "ticket": "免费"},

    # === 更多 主题乐园 ===
    {"name": "北京环球影城", "province": "北京", "city": "北京", "category": "主题乐园",
     "description": "亚洲第三座环球影城主题公园，哈利·波特魔法世界、变形金刚基地等七大主题区。", "highlights": "哈利·波特禁忌之旅、变形金刚火种源、水世界表演、侏罗纪大冒险",
     "best_season": "春秋两季", "tips": "建议购买优速通，热门项目排队时间长。", "rating": 4.6, "ticket": "418元"},
    {"name": "广州长隆欢乐世界", "province": "广东", "city": "广州", "category": "主题乐园",
     "description": "中国最大的综合性主题乐园之一，拥有众多世界级过山车和游乐设施。", "highlights": "垂直过山车、十环过山车、U型滑板、超级大摆锤",
     "best_season": "四季皆宜", "tips": "建议工作日前往，周末人多。", "rating": 4.4, "ticket": "250元"},
    {"name": "欢乐谷（深圳）", "province": "广东", "city": "深圳", "category": "主题乐园",
     "description": "中国最大的连锁主题乐园品牌，深圳欢乐谷是旗舰店，有九大主题区。", "highlights": "雪域雄鹰过山车、金矿漂流、玛雅水公园、魔幻城堡",
     "best_season": "四季皆宜", "tips": "夏季水公园开放，适合玩水。", "rating": 4.3, "ticket": "230元"},
    {"name": "中华恐龙园", "province": "江苏", "city": "常州", "category": "主题乐园",
     "description": "中国最大的恐龙主题乐园，集科普、游乐、演艺于一体，是亲子游的热门目的地。", "highlights": "中华恐龙馆、4D过山龙、恐龙水世界、梦幻庄园",
     "best_season": "四季皆宜", "tips": "科普与娱乐结合，非常适合带孩子去。", "rating": 4.4, "ticket": "260元"},
    {"name": "华强方特（芜湖）", "province": "安徽", "city": "芜湖", "category": "主题乐园",
     "description": "以中国文化为主题的大型高科技主题乐园，将中国故事与现代科技完美融合。", "highlights": "女娲补天、孟姜女、牛郎织女、飞翔之歌",
     "best_season": "春秋两季", "tips": "室内项目多，不受天气影响。", "rating": 4.3, "ticket": "280元"},
    {"name": "海昌海洋公园（上海）", "province": "上海", "city": "上海", "category": "主题乐园",
     "description": "上海最大的海洋主题公园，拥有企鹅馆、鲨鱼馆、珊瑚礁馆等五大主题区。", "highlights": "虎鲸表演、企鹅馆、海底隧道、过山车",
     "best_season": "四季皆宜", "tips": "虎鲸表演非常震撼，提前占座。", "rating": 4.4, "ticket": "360元"},
    {"name": "重庆融创文旅城", "province": "重庆", "city": "重庆", "category": "主题乐园",
     "description": "重庆最大的文旅综合体，集主题乐园、雪世界、水世界于一体。", "highlights": "飞越重庆、雪世界滑雪、水世界、渝乐小镇",
     "best_season": "四季皆宜", "tips": "雪世界可以在南方体验滑雪。", "rating": 4.2, "ticket": "200元"},
    {"name": "方特东盟神画（南宁）", "province": "广西", "city": "南宁", "category": "主题乐园",
     "description": "以东南亚文化为主题的高科技主题乐园，一园看遍东南亚十国风情。", "highlights": "走进吴哥、拉玛传奇、塔銮盛典、千岛之歌",
     "best_season": "四季皆宜", "tips": "千岛之歌演出非常震撼。", "rating": 4.3, "ticket": "280元"},

    # === 更多 自然风光 ===
    {"name": "丹霞山", "province": "广东", "city": "韶关", "category": "自然风光",
     "description": "世界自然遗产，丹霞地貌的命名地，红色砂岩山峰在阳光下如火焰般绚烂。", "highlights": "阳元石、阴元石、长老峰、锦江竹筏",
     "best_season": "3-5月、9-11月", "tips": "春秋两季是最佳游览季节。", "rating": 4.5, "ticket": "100元"},
    {"name": "天山天池", "province": "新疆", "city": "昌吉", "category": "自然风光",
     "description": "古称瑶池，天山博格达峰下的高山冰碛湖，湖水碧蓝如宝石。", "highlights": "天池湖景、马牙山索道、西王母庙、博格达峰",
     "best_season": "6-9月", "tips": "山上气温低，带件外套。", "rating": 4.5, "ticket": "155元"},
    {"name": "崂山", "province": "山东", "city": "青岛", "category": "自然风光",
     "description": "海上第一名山，道教名山，山海相连的独特景致令人流连忘返。", "highlights": "太清宫、巨峰、仰口海滩、北九水",
     "best_season": "4-10月", "tips": "崂山分为多条游览线路，建议选1-2条。", "rating": 4.5, "ticket": "120元"},
    {"name": "大别山", "province": "安徽", "city": "六安", "category": "自然风光",
     "description": "中国革命圣地，横跨鄂豫皖三省的壮丽山脉，自然风光与红色文化交相辉映。", "highlights": "天堂寨、白马尖、燕子河大峡谷、红色旧址",
     "best_season": "5-10月", "tips": "天堂寨是大别山的精华景点。", "rating": 4.3, "ticket": "100元"},
    {"name": "泸沽湖", "province": "云南", "city": "丽江", "category": "自然风光",
     "description": "云南海拔最高的湖泊，摩梭人的故乡，湖水清澈见底，被誉为\"高原明珠\"。", "highlights": "里格半岛、走婚桥、草海、猪槽船游湖",
     "best_season": "3-6月、9-11月", "tips": "建议住湖边的民宿，看日出和星空。", "rating": 4.7, "ticket": "70元"},
    {"name": "海螺沟冰川", "province": "四川", "city": "甘孜", "category": "自然风光",
     "description": "距离城市最近的现代冰川，可以近距离接触冰川，同时欣赏贡嘎雪山的壮丽。", "highlights": "冰川舌、大冰瀑布、贡嘎雪山、温泉",
     "best_season": "10-4月", "tips": "冬季和春季冰川更壮观。", "rating": 4.5, "ticket": "160元"},
    {"name": "苍山洱海", "province": "云南", "city": "大理", "category": "自然风光",
     "description": "大理的灵魂，苍山十九峰十八溪，洱海碧波万顷，风花雪月的大理由此得名。", "highlights": "苍山索道、洱海骑行、喜洲古镇、双廊",
     "best_season": "3-10月", "tips": "环洱海一圈约120公里，建议分两天。", "rating": 4.6, "ticket": "免费"},
    {"name": "巴松措", "province": "西藏", "city": "林芝", "category": "自然风光",
     "description": "西藏唯一的5A级自然风景区，湖心岛上的措宗寺已有1500年历史。", "highlights": "湖心岛、措宗寺、结巴村、雪山倒影",
     "best_season": "6-9月", "tips": "林芝海拔较低，高原反应较轻。", "rating": 4.5, "ticket": "120元"},

    # === 更多 历史文化 ===
    {"name": "平遥古城", "province": "山西", "city": "晋中", "category": "历史文化",
     "description": "中国保存最完整的古代县城，也是中国最早的银行\"日升昌\"票号所在地。", "highlights": "古县衙、日升昌票号、文庙、古城墙",
     "best_season": "5-10月", "tips": "建议住古城内的民宿体验晋商文化。", "rating": 4.5, "ticket": "125元"},
    {"name": "少林寺", "province": "河南", "city": "郑州", "category": "历史文化",
     "description": "天下功夫出少林，中国佛教禅宗祖庭，少林武术的发源地。", "highlights": "少林功夫表演、塔林、藏经阁、初祖庵",
     "best_season": "春秋两季", "tips": "一定要看少林功夫表演，每天多场。", "rating": 4.5, "ticket": "100元"},
    {"name": "白马寺", "province": "河南", "city": "洛阳", "category": "历史文化",
     "description": "中国第一古刹，佛教传入中国后兴建的第一座寺院，有中国佛教的\"祖庭\"之称。", "highlights": "大雄殿、齐云塔、国际佛殿区、唐代遗址",
     "best_season": "春秋两季", "tips": "国际佛殿区有泰国、印度、缅甸风格佛殿。", "rating": 4.4, "ticket": "35元"},
    {"name": "丽江古城", "province": "云南", "city": "丽江", "category": "历史文化",
     "description": "世界文化遗产，茶马古道上的重镇，小桥流水的纳西族古城，被誉为\"东方威尼斯\"。", "highlights": "四方街、木府、大水车、黑龙潭",
     "best_season": "四季皆宜", "tips": "清晨的古城最安静美好。", "rating": 4.4, "ticket": "免费（古城维护费50元）"},
    {"name": "大理古城", "province": "云南", "city": "大理", "category": "历史文化",
     "description": "南诏国和大理国的都城，苍山脚下洱海之滨，文艺青年的心灵归宿。", "highlights": "五华楼、洋人街、人民路、崇圣寺三塔",
     "best_season": "3-10月", "tips": "古城内有很多特色小店和咖啡馆。", "rating": 4.3, "ticket": "免费"},
    {"name": "都江堰", "province": "四川", "city": "成都", "category": "历史文化",
     "description": "世界文化遗产，2000多年前李冰父子修建的水利工程，至今仍在发挥作用。", "highlights": "鱼嘴、飞沙堰、宝瓶口、二王庙、安澜索桥",
     "best_season": "四季皆宜", "tips": "建议请讲解，了解水利工程的精妙。", "rating": 4.6, "ticket": "80元"},
    {"name": "乐山大佛", "province": "四川", "city": "乐山", "category": "历史文化",
     "description": "世界最大的石刻弥勒佛坐像，高71米，建于唐代，历经90年完成。", "highlights": "大佛全身像、九曲栈道、凌云寺、乌尤寺",
     "best_season": "春秋两季", "tips": "建议乘船远观大佛全景再登栈道近看。", "rating": 4.6, "ticket": "80元"},
    {"name": "塔尔寺", "province": "青海", "city": "西宁", "category": "历史文化",
     "description": "藏传佛教格鲁派六大寺院之一，宗喀巴大师的诞生地，以酥油花、壁画、堆绣闻名。", "highlights": "大金瓦殿、酥油花馆、八宝如意塔、大经堂",
     "best_season": "6-8月", "tips": "寺内不允许拍照，尊重宗教信仰。", "rating": 4.5, "ticket": "70元"},
    {"name": "南普陀寺", "province": "福建", "city": "厦门", "category": "历史文化",
     "description": "闽南佛教圣地，依山而建，香火鼎盛，与厦门大学相邻。", "highlights": "大雄宝殿、藏经阁、五老峰、素斋",
     "best_season": "四季皆宜", "tips": "寺院的素斋很有名，值得一试。", "rating": 4.4, "ticket": "免费"},
    {"name": "寒山寺", "province": "江苏", "city": "苏州", "category": "历史文化",
     "description": "因张继《枫桥夜泊》而闻名天下，'姑苏城外寒山寺，夜半钟声到客船'千古传诵。", "highlights": "寒山寺钟楼、枫桥、大雄宝殿、碑廊",
     "best_season": "四季皆宜", "tips": "新年敲钟活动非常有名。", "rating": 4.3, "ticket": "20元"},
    {"name": "岳飞庙", "province": "河南", "city": "安阳", "category": "历史文化",
     "description": "纪念南宋抗金名将岳飞的祠庙，精忠报国的精神传承千年。", "highlights": "岳飞塑像、秦桧跪像、精忠柏、岳飞纪念馆",
     "best_season": "四季皆宜", "tips": "了解岳飞生平，感受爱国精神。", "rating": 4.3, "ticket": "40元"},
    {"name": "鲁迅故里", "province": "浙江", "city": "绍兴", "category": "历史文化",
     "description": "中国现代文学巨匠鲁迅的出生地和成长地，百草园和三味书屋是课本里的经典场景。", "highlights": "百草园、三味书屋、鲁迅纪念馆、咸亨酒店",
     "best_season": "四季皆宜", "tips": "可以在咸亨酒店尝一尝茴香豆。", "rating": 4.4, "ticket": "免费"},
    {"name": "滕王阁", "province": "江西", "city": "南昌", "category": "历史文化",
     "description": "江南三大名楼之一，因王勃《滕王阁序》名垂千古，'落霞与孤鹜齐飞，秋水共长天一色'。", "highlights": "滕王阁主阁、赣江观景、诗词碑廊、VR体验",
     "best_season": "四季皆宜", "tips": "登阁可俯瞰赣江和南昌城市风光。", "rating": 4.4, "ticket": "50元"},

    # === 辽宁（补齐） ===
    {"name": "大连星海广场", "province": "辽宁", "city": "大连", "category": "都市风情",
     "description": "亚洲最大的城市广场，面向大海，百年城雕和音乐喷泉是大连的城市名片。", "highlights": "百年城雕、音乐喷泉、星海湾大桥、会展中心",
     "best_season": "5-10月", "tips": "晚上音乐喷泉很壮观。", "rating": 4.3, "ticket": "免费"},
    {"name": "本溪水洞", "province": "辽宁", "city": "本溪", "category": "自然风光",
     "description": "世界最长的地下充水溶洞，钟乳石千姿百态，乘船游览地下河宛如仙境。", "highlights": "地下河乘船、钟乳石奇观、玉象戏水、银河两岸",
     "best_season": "四季皆宜", "tips": "洞内常年恒温，冬暖夏凉。", "rating": 4.4, "ticket": "70元"},
    {"name": "大连金石滩", "province": "辽宁", "city": "大连", "category": "自然风光",
     "description": "大连最美的海滨度假区，奇石嶙峋的海岸线堪称\"地质博物馆\"。", "highlights": "金石滩地质公园、黄金海岸、发现王国、滨海国家地质公园",
     "best_season": "5-10月", "tips": "建议游玩一整天。", "rating": 4.3, "ticket": "免费（部分景区收费）"},

    # === 宁夏（补齐） ===
    {"name": "水洞沟", "province": "宁夏", "city": "银川", "category": "历史文化",
     "description": "中国最早发现的旧石器时代遗址之一，也是中国唯一保存最完整的万里长城军事防御体系。", "highlights": "藏兵洞、遗址博物馆、长城遗址、芦花谷",
     "best_season": "5-10月", "tips": "藏兵洞非常有趣，机关重重。", "rating": 4.3, "ticket": "60元"},
    {"name": "贺兰山岩画", "province": "宁夏", "city": "银川", "category": "历史文化",
     "description": "贺兰山中的远古岩画艺术宝库，记录了远古先民的生活和信仰，被称为\"石头上的史书\"。", "highlights": "太阳神岩画、狩猎图、贺兰山风光、韩美林艺术馆",
     "best_season": "5-10月", "tips": "韩美林艺术馆也很值得参观。", "rating": 4.3, "ticket": "70元"},

    # === 香港（补齐） ===
    {"name": "太平山顶", "province": "香港", "city": "香港", "category": "自然风光",
     "description": "香港岛最高点，乘坐山顶缆车可俯瞰维多利亚港和九龙半岛全景。", "highlights": "凌霄阁观景台、山顶缆车、杜莎夫人蜡像馆、山顶步道",
     "best_season": "四季皆宜", "tips": "傍晚时分上山，可同时欣赏日落和夜景。", "rating": 4.6, "ticket": "缆车往返88港币"},
    {"name": "南丫岛", "province": "香港", "city": "香港", "category": "自然风光",
     "description": "香港第三大岛，远离城市喧嚣的宁静渔村，徒步和海鲜是这里的主题。", "highlights": "榕树湾、索罟湾、洪圣爷湾泳滩、徒步径",
     "best_season": "10-4月", "tips": "从榕树湾徒步到索罟湾约1.5小时。", "rating": 4.3, "ticket": "免费"},

    # === 澳门（补齐） ===
    {"name": "澳门旅游塔", "province": "澳门", "city": "澳门", "category": "现代建筑",
     "description": "澳门地标建筑，高338米，全球最高蹦极跳就在此，自由落体233米。", "highlights": "观光层、蹦极跳、空中漫步、360度旋转餐厅",
     "best_season": "四季皆宜", "tips": "喜欢刺激的可以挑战蹦极。", "rating": 4.3, "ticket": "165澳币"},
    {"name": "路氹金光大道", "province": "澳门", "city": "澳门", "category": "都市风情",
     "description": "澳门最繁华的娱乐区，汇集了威尼斯人、巴黎人、永利皇宫等世界级度假村。", "highlights": "威尼斯人运河、巴黎铁塔、永利喷泉、新濠影汇8字摩天轮",
     "best_season": "四季皆宜", "tips": "晚上的灯光秀非常华丽。", "rating": 4.4, "ticket": "免费"},

    # === 吉林（补齐） ===
    {"name": "高句丽王城", "province": "吉林", "city": "通化", "category": "历史文化",
     "description": "世界文化遗产，高句丽王朝的遗迹，将军坟被誉为\"东方金字塔\"。", "highlights": "将军坟、好太王碑、丸都山城、博物馆",
     "best_season": "5-10月", "tips": "好太王碑是研究高句丽历史的重要文物。", "rating": 4.2, "ticket": "100元"},

    # === 安徽（补齐） ===
    {"name": "天柱山", "province": "安徽", "city": "安庆", "category": "自然风光",
     "description": "世界地质公园，五岳之外又一名山，以奇峰怪石和云海闻名。", "highlights": "天柱峰、炼丹湖、神秘谷、天柱山云海",
     "best_season": "4-10月", "tips": "山上住宿有限，建议一日游。", "rating": 4.5, "ticket": "130元"},

    # === 山东（补齐） ===
    {"name": "蓬莱阁", "province": "山东", "city": "烟台", "category": "历史文化",
     "description": "八仙过海的传说发生地，中国四大名楼之一，仙气缭绕的海边楼阁。", "highlights": "蓬莱阁古建筑群、田横山、八仙过海景区、三仙山",
     "best_season": "5-10月", "tips": "海市蜃楼奇观可遇不可求。", "rating": 4.4, "ticket": "100元"},

    # === 海南（补齐） ===
    {"name": "蜈支洲岛", "province": "海南", "city": "三亚", "category": "自然风光",
     "description": "中国最美潜水胜地之一，海水清澈见底，海底珊瑚丰富，被誉为\"中国的马尔代夫\"。", "highlights": "潜水、摩托艇、情人桥、观日岩",
     "best_season": "9-4月", "tips": "潜水建议上午进行，水质更清澈。", "rating": 4.6, "ticket": "144元"},

    # === 西藏（补齐） ===
    {"name": "羊卓雍措", "province": "西藏", "city": "山南", "category": "自然风光",
     "description": "西藏三大圣湖之一，湖水在阳光下呈现出梦幻的蓝色，被誉为\"天上的仙境\"。", "highlights": "羊湖观景台、日托寺、环湖公路、岗巴拉山口",
     "best_season": "6-9月", "tips": "海拔4400米，注意高反。", "rating": 4.8, "ticket": "60元"},

    # === 陕西（补齐） ===
    {"name": "黄帝陵", "province": "陕西", "city": "延安", "category": "历史文化",
     "description": "中华民族始祖轩辕黄帝的陵寝，海内外华人寻根祭祖的圣地。", "highlights": "轩辕庙、黄帝陵冢、祭祀广场、古柏群",
     "best_season": "四季皆宜", "tips": "每年清明节的公祭典礼最为隆重。", "rating": 4.4, "ticket": "75元"},
    {"name": "太白山", "province": "陕西", "city": "宝鸡", "category": "自然风光",
     "description": "秦岭最高峰，海拔3771米，青藏高原以东第一高峰，六月积雪成为奇观。", "highlights": "拔仙台、大爷海、天圆地方、莲花峰瀑布",
     "best_season": "6-10月", "tips": "登山需做好高原反应准备。", "rating": 4.5, "ticket": "90元"},

    # === 河北（补齐） ===
    {"name": "正定古城", "province": "河北", "city": "石家庄", "category": "历史文化",
     "description": "中国古代建筑艺术的宝库，隆兴寺、临济寺、凌霄塔等千年古建密集。", "highlights": "隆兴寺大佛、临济寺、凌霄塔、古城墙",
     "best_season": "春夏秋三季", "tips": "隆兴寺是中国现存最大的宋代佛教建筑群。", "rating": 4.4, "ticket": "50元"},
    {"name": "白洋淀", "province": "河北", "city": "保定", "category": "自然风光",
     "description": "华北最大的淡水湖，荷花盛开时节景象壮美，也是红色经典《小兵张嘎》的故事发生地。", "highlights": "荷花大观园、白洋淀文化苑、嘎子村、芦苇荡",
     "best_season": "7-9月（荷花季）", "tips": "7-8月荷花盛开是最佳季节。", "rating": 4.2, "ticket": "免费（部分景点收费）"},
]

def main():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        attractions = json.load(f)

    existing_names = {a["name"] for a in attractions}
    next_id = max(a["id"] for a in attractions) + 1

    total_added = 0
    for expansions_list in [EXPANSIONS, EXPANSIONS_2]:
        added = 0
        for item in expansions_list:
            if item["name"] not in existing_names:
                new_att = {
                    "id": next_id,
                    "name": item["name"],
                    "province": item["province"],
                    "city": item.get("city", ""),
                    "category": item["category"],
                    "description": item.get("description", ""),
                    "highlights": item.get("highlights", ""),
                    "best_season": item.get("best_season", ""),
                    "tips": item.get("tips", ""),
                    "rating": item.get("rating", 4.0),
                    "ticket": item.get("ticket", ""),
                    "basic_info": "",
                    "travel_guide": "",
                    "transport": "",
                    "food": "",
                    "culture": "",
                    "related_ids": [],
                    "location": None,
                }
                attractions.append(new_att)
                existing_names.add(item["name"])
                next_id += 1
                added += 1
        total_added += added

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(attractions, f, ensure_ascii=False, indent=2)

    # 统计
    from collections import Counter
    prov_count = Counter(a["province"] for a in attractions)
    cat_count = Counter(a["category"] for a in attractions)

    print(f"原数据: {len(attractions) - total_added} 个景点")
    print(f"本次新增: {total_added} 个景点")
    print(f"总计: {len(attractions)} 个景点\n")
    print("省份分布:")
    for p, c in prov_count.most_common():
        print(f"  {p}: {c}")
    print("\n分类分布:")
    for c, n in cat_count.most_common():
        print(f"  {c}: {n}")


if __name__ == "__main__":
    main()
