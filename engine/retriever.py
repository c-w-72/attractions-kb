"""
增强检索引擎
- jieba 中文分词
- 字段加权 TF-IDF 检索
- FAISS 语义索引 (默认优先)
- LRU 查询缓存
- 概念查询扩展（"看海" → 海滩/海滨等关键词）
"""

import json
import logging
import os
import pickle
import threading
from functools import lru_cache
from typing import Optional

import numpy as np

from engine.monitor import Timer

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DATA_FILE = os.path.join(DATA_DIR, "attractions.json")
CACHE_DIR = os.path.join(DATA_DIR, "cache")

# 字段权重
FIELD_WEIGHTS = {
    "name": 5.0,
    "highlights": 3.0,
    "province": 2.0,
    "city": 2.0,
    "category": 1.5,
    "description": 1.0,
    "tips": 1.0,
    "food": 1.2,
    "culture": 1.2,
    "basic_info": 1.0,
    "travel_guide": 1.0,
    "transport": 1.0,
}


# 概念查询 → 扩展关键词（短查询匹配不足时自动补充）
QUERY_EXPANSIONS = {
    "看海": "海滩 海滨 海岸 海岛 海景 赶海 海边 三亚 青岛 厦门 北海",
    "海边": "海滩 海滨 海岸 海岛 海景 赶海 海边 三亚 青岛 厦门 北海",
    "海滩": "海滩 海滨 海岸 海景 三亚 青岛 厦门 北海",
    "爬山": "登山 山峰 山岳 自然风光 徒步 黄山 泰山 华山 峨眉山",
    "登山": "登山 山峰 山岳 自然风光 徒步 黄山 泰山 华山 峨眉山",
    "古镇": "古镇 古城 古村 历史文化 丽江 凤凰 平遥 周庄 乌镇",
    "避暑": "避暑 清凉 夏季 凉爽 承德 庐山 峨眉山 长白山 九寨沟",
    "赏花": "赏花 花海 花卉 春季 樱花 桃花 梅花 牡丹 油菜花",
    "亲子": "亲子 儿童 乐园 动物园 主题乐园 迪士尼 欢乐谷",
    "拍照": "拍照 摄影 打卡 网红 风景 取景 胜地",
    "免费": "免费 免票 0元 免费开放",
    "夜景": "夜景 灯光 夜景 夜游 城市夜景 观光 外滩",
    "美食": "美食 小吃 特色美食 餐饮 步行街 夜市",
    "日出": "日出 观日出 山顶 清晨 黄山 泰山",
    "冬季": "冬季 滑雪 温泉 雪景 哈尔滨 长白山",
    "夏季": "夏季 避暑 海滩 漂流 水上 清凉",
}


class AttractionRetriever:
    """增强版旅游景点检索器"""
    _COASTAL_CITIES = {"三亚", "青岛", "厦门", "大连", "北海", "威海", "烟台", "秦皇岛", "珠海", "海口", "深圳"}

    def __init__(self, data_path: str = None):
        self.data_path = data_path or DATA_FILE
        self.attractions = self._load_data()
        self._vectorizers = {}  # field -> (vec, matrix)
        self._tokenizer = None
        self._province_index = {}   # province -> [att, ...]
        self._category_index = {}   # category -> [att, ...]
        self._name_index = {}       # name -> att
        self._id_index = {}         # id -> att
        self._build_indices()
        os.makedirs(CACHE_DIR, exist_ok=True)

    def _build_indices(self):
        """预建倒排索引，加速筛选"""
        self._pinyin_cache = {}  # name -> pinyin_str
        for a in self.attractions:
            # 省份索引
            p = a["province"]
            if p not in self._province_index:
                self._province_index[p] = []
            self._province_index[p].append(a)

            # 分类索引
            c = a["category"]
            if c not in self._category_index:
                self._category_index[c] = []
            self._category_index[c].append(a)

            # 名称/ID 索引
            self._name_index[a["name"]] = a
            self._id_index[a["id"]] = a

    def _load_data(self) -> list:
        with open(self.data_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _get_tokenizer(self):
        """延迟加载 jieba 分词器"""
        if self._tokenizer is None:
            import jieba
            jieba.setLogLevel(20)
            self._tokenizer = jieba
            # 加载景点名词典
            for att in self.attractions:
                jieba.add_word(att["name"], freq=100, tag="ns")
                for h in att.get("highlights", "").split("、"):
                    h = h.strip()
                    if len(h) >= 2:
                        jieba.add_word(h, freq=50)
        return self._tokenizer

    def _tokenize(self, text: str) -> str:
        """分词并用空格连接"""
        try:
            tok = self._get_tokenizer()
            return " ".join(tok.cut(text))
        except ImportError:
            return text

    def _build_field_text(self, att: dict, field: str) -> str:
        """构建某个字段的检索文本"""
        raw = att.get(field, "")
        if isinstance(raw, str) and raw:
            if field in ("name", "province", "city", "category"):
                return raw
            return raw
        return ""

    def build_index(self, use_semantic: bool = False, progress_callback=None):
        """构建索引（自动从缓存加载或重建）
        Args:
            use_semantic: 是否尝试构建语义索引
            progress_callback: 可选进度回调 fn(percent: int, message: str)
        """
        self._build_weighted_tfidf(progress_callback=progress_callback)
        if use_semantic:
            self._try_build_semantic()
            if progress_callback:
                progress_callback(100, "✅ 索引构建完成")

    def _get_tokenized_docs(self, fields: list, progress_callback=None) -> dict:
        """获取或缓存分词后的文档列表"""
        cache_path = os.path.join(CACHE_DIR, "tokenized_docs.pkl")

        # 尝试从缓存加载
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "rb") as f:
                    cached = pickle.load(f)
                if cached.get("count") == len(self.attractions) and cached.get("fields") == fields:
                    return cached["docs"]
            except Exception as e:
                logger.warning("缓存读取失败: %s", e)

        # 逐字段分词
        docs_dict = {}
        total = len(fields)
        for fi, field in enumerate(fields):
            docs = []
            for a in self.attractions:
                text = self._build_field_text(a, field)
                docs.append(self._tokenize(text))
            docs_dict[field] = docs
            if progress_callback:
                progress_callback(int((fi + 1) / total * 40), f"🔧 分词中 ({field})...")

        # 缓存到磁盘
        try:
            with open(cache_path, "wb") as f:
                pickle.dump({"count": len(self.attractions), "fields": fields, "docs": docs_dict}, f)
        except Exception as e:
            logger.warning("分词缓存写入失败: %s", e)

        return docs_dict

    def _build_weighted_tfidf(self, progress_callback=None):
        """构建加权 TF-IDF 索引，按字段分别向量化"""
        from sklearn.feature_extraction.text import TfidfVectorizer
        from scipy import sparse
        import gzip

        cache_path = os.path.join(CACHE_DIR, "weighted_index.pkl")
        cache_path_gz = cache_path + ".gz"

        # 尝试从缓存加载（优先 .gz，回退旧格式）
        load_path = cache_path_gz if os.path.exists(cache_path_gz) else (cache_path if os.path.exists(cache_path) else None)
        if load_path:
            try:
                if load_path.endswith(".gz"):
                    with gzip.open(load_path, "rb") as f:
                        data = pickle.load(f)
                else:
                    with open(load_path, "rb") as f:
                        data = pickle.load(f)
                if data.get("version") == 3 and data.get("count") == len(self.attractions):
                    self._vectorizers = data["vectorizers"]
                    self._weighted_matrix = data["matrix"]
                    self._feature_fields = data["fields"]
                    self._use_semantic = False
                    if progress_callback:
                        progress_callback(100, "✅ 从缓存加载索引完成")
                    return
            except Exception as e:
                logger.warning("索引缓存读取失败: %s", e)

        self._weighted_matrix = None
        self._feature_fields = [f for f in FIELD_WEIGHTS if any(a.get(f, "") for a in self.attractions)]

        # 获取分词后的文档（优先使用缓存）
        docs_dict = self._get_tokenized_docs(self._feature_fields, progress_callback=progress_callback)

        matrices = []
        self._vectorizers = {}

        total = len(self._feature_fields)
        for fi, field in enumerate(self._feature_fields):
            docs = docs_dict[field]

            vec = TfidfVectorizer(
                analyzer="word" if field in ("description", "food", "culture",
                                             "basic_info", "travel_guide", "tips") else "char",
                ngram_range=(1, 2) if field in ("name", "province", "city", "category") else (2, 4),
                max_features=5000,
                sublinear_tf=True,
                min_df=1,
            )
            matrix = vec.fit_transform(docs)
            self._vectorizers[field] = vec
            matrices.append(matrix * FIELD_WEIGHTS[field])

            if progress_callback:
                pct = 40 + int((fi + 1) / total * 55)
                progress_callback(pct, f"🔬 向量化 {field}...")

        self._weighted_matrix = sparse.hstack(matrices) if len(matrices) > 1 else matrices[0]

        # 缓存到磁盘（gzip 压缩）
        try:
            import gzip
            # 先删除旧格式缓存
            for old in [cache_path, cache_path + ".gz"]:
                if os.path.exists(old):
                    os.remove(old)
            with gzip.open(cache_path_gz, "wb", compresslevel=3) as f:
                pickle.dump({
                    "version": 3,
                    "count": len(self.attractions),
                    "matrix": self._weighted_matrix,
                    "vectorizers": self._vectorizers,
                    "fields": self._feature_fields,
                }, f)
        except Exception as e:
            logger.warning("索引缓存写入失败: %s", e)

        self._use_semantic = False
        if progress_callback:
            progress_callback(100, "✅ 索引构建完成")

        # 后台预计算拼音 + 预热缓存
        self._precompute_pinyin()
        self._warm_cache()

    def _warm_cache(self):
        """后台预热常用查询缓存"""
        common_queries = [
            "北京", "上海", "广州", "自然风光", "历史文化",
            "免费", "爬山", "看海", "避暑", "古镇",
        ]
        try:
            for q in common_queries:
                self._tfidf_search(q)
            logger.info("缓存预热完成 (%d 个常用查询)", len(common_queries))
        except Exception as e:
            logger.warning("缓存预热异常: %s", e)

    def search(
            self,
            query: str,
            top_k: int = 5,
            province: Optional[str] = None,
            category: Optional[str] = None,
            min_rating: Optional[float] = None,
    ) -> list:
        """检索 — FAISS 优先, TF-IDF 回退, 自动概念扩展"""
        with Timer("search"):
            results = self._search_with_expansion(query, top_k)

            filtered = []
            for att, score in results:
                if province and att["province"] != province:
                    continue
                if category and att["category"] != category:
                    continue
                if min_rating and att.get("rating", 0) < min_rating:
                    continue
                filtered.append((att, score))
                if len(filtered) >= top_k:
                    break

            return filtered[:top_k]

    def _search_with_expansion(self, query: str, top_k: int) -> list:
        """检索 + 概念查询扩展"""
        query_lower = query.strip().lower()

        if hasattr(self, '_faiss_index'):
            results = self._faiss_search(query, top_k * 4)
        else:
            results = self._tfidf_search(query)[:top_k * 4]

        # 命中了概念词 → 总执行扩展并重排（短句字面匹配不靠谱，如"看海"会误配"上海"）
        if query_lower in QUERY_EXPANSIONS:
            expanded = QUERY_EXPANSIONS[query_lower]
            if hasattr(self, '_faiss_index'):
                ext_results = self._faiss_search(expanded, top_k * 3)
            else:
                ext_results = self._tfidf_search(expanded)[:top_k * 3]

            # RRF 融合：扩展结果排前，原查询结果插空
            seen = set(a["id"] for a, _ in results)
            merged = list(results)
            for att, score in ext_results:
                if att["id"] not in seen:
                    seen.add(att["id"])
                    merged.append((att, score * 0.85))  # 扩展结果略降权
                    if len(merged) >= top_k * 3:
                        break

            # 概念搜索重排：提升与查询语义真正相关的景点
            if query_lower in QUERY_EXPANSIONS:
                merged = self._rerank_concept(merged, query_lower, top_k * 3)
            results = merged

        return results[:top_k * 4]

    def _rerank_concept(self, results: list, concept: str, top_k: int) -> list:
        """概念搜索结果重排：提升语义相关度（乘性重打分）"""
        # 定义评分乘子，不相关景点降权而非不相关景点提权
        reranked = []
        for att, score in results:
            factor = 1.0
            desc = (att.get("description", "") + att.get("highlights", "") +
                    att.get("name", "") + att.get("category", ""))
            city = att.get("city", "")
            name = att["name"]

            if concept in ("看海", "海边", "海滩"):
                # 海滩/海滨关键词 → 强保留；沿海城市且分类相关 → 中保留
                if any(kw in desc for kw in ("海滩", "海滨", "海岸", "海景", "赶海", "海浪", "海风")):
                    factor = 1.8
                elif city in self._COASTAL_CITIES and att["category"] in ("自然风光", "都市风情", "主题乐园"):
                    factor = 1.3
                elif "上海" in name or "上海" in city:
                    factor = 0.3
                else:
                    factor = 0.2
            elif concept == "爬山":
                if any(kw in desc for kw in ("登山", "山峰", "山岳", "山")):
                    factor = 1.5
                elif att["category"] == "自然风光":
                    factor = 1.2
            elif concept == "古镇":
                if any(kw in desc for kw in ("古镇", "古城", "古村", "民俗")):
                    factor = 1.5
                elif att["category"] == "历史文化":
                    factor = 1.2

            reranked.append((att, score * factor))

        reranked.sort(key=lambda x: -x[1])
        return reranked[:top_k]

    @lru_cache(maxsize=64)
    def _tfidf_search(self, query: str) -> list:
        """TF-IDF 加权检索 (缓存)"""
        from sklearn.metrics.pairwise import cosine_similarity

        query_vecs = []
        for field in self._feature_fields:
            vec = self._vectorizers.get(field)
            if vec is None:
                continue
            qv = vec.transform([self._tokenize(query)])
            query_vecs.append(qv * FIELD_WEIGHTS[field])

        from scipy import sparse
        full_query = sparse.hstack(query_vecs)
        scores = cosine_similarity(full_query, self._weighted_matrix).flatten()

        top_indices = scores.argsort()[-50:][::-1]
        return [
            (self.attractions[i], float(scores[i]))
            for i in top_indices
            if scores[i] > 0.001
        ]

    # ---- 语义检索（可选） ----
    def _try_build_semantic(self) -> bool:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            return False

        model_name = "shibing624/text2vec-base-chinese"
        try:
            self._embedder = SentenceTransformer(model_name, device="cpu")
            texts = [f"{a['name']}。{a.get('description','')}" for a in self.attractions]
            cache_path = os.path.join(CACHE_DIR, "semantic_emb.npy")
            if os.path.exists(cache_path):
                embeddings = np.load(cache_path)
            else:
                embeddings = self._embedder.encode(texts, show_progress_bar=True)
                np.save(cache_path, embeddings)
            self._semantic_embeddings = np.array(embeddings).astype("float32")
            self._semantic_embeddings /= np.linalg.norm(self._semantic_embeddings, axis=1, keepdims=True)
            self._semantic_embedder = self._embedder
            # 自动构建 FAISS 索引
            self._build_faiss_index()
            return True
        except Exception as e:
                logger.debug("语义模型加载失败: %s", e)

        return False

    def _build_faiss_index(self) -> bool:
        """构建 FAISS 索引加速语义检索"""
        try:
            import faiss
        except ImportError:
            return False

        if not hasattr(self, '_semantic_embeddings'):
            return False

        dim = self._semantic_embeddings.shape[1]
        index = faiss.IndexFlatIP(dim)
        index.add(self._semantic_embeddings.astype(np.float32))
        self._faiss_index = index
        return True

    def _faiss_search(self, query: str, top_k: int) -> list:
        """FAISS 语义检索"""
        if not hasattr(self, '_faiss_index'):
            return []

        emb = self._semantic_embedder.encode([query])
        emb = np.array(emb).astype("float32")
        emb /= np.linalg.norm(emb)
        scores, indices = self._faiss_index.search(emb, min(top_k, len(self.attractions)))
        return [(self.attractions[i], float(scores[0][j]))
                for j, i in enumerate(indices[0])
                if 0 <= i < len(self.attractions)]

    # ---- 辅助方法 ----
    def hybrid_search(self, query: str, top_k: int = 5, province=None, category=None, min_rating=None) -> list:
        """混合检索：FAISS 语义 + TF-IDF RRF 融合（含概念扩展）"""
        with Timer("hybrid_search"):
            base_results = self._search_with_expansion(query, top_k * 3)

            has_faiss = hasattr(self, '_faiss_index')
            if not has_faiss:
                # 无 FAISS 时退化为普通搜索
                filtered = []
                for att, score in base_results:
                    if province and att["province"] != province:
                        continue
                    if category and att["category"] != category:
                        continue
                    if min_rating and att.get("rating", 0) < min_rating:
                        continue
                    filtered.append((att, score))
                    if len(filtered) >= top_k:
                        break
                return filtered[:top_k]

            sem_results = self._faiss_search(query, top_k * 3)

            # RRF 融合：TF-IDF 概念扩展 + FAISS
            scores = {}
            for i, (att, s) in enumerate(base_results):
                scores[att["id"]] = scores.get(att["id"], 0) + 1.0 / (i + 60)
            for i, (att, s) in enumerate(sem_results):
                scores[att["id"]] = scores.get(att["id"], 0) + 1.0 / (i + 60)

            ranked = sorted(
                [(self.get_by_id(aid), sc) for aid, sc in scores.items()],
                key=lambda x: -x[1],
            )

            filtered = []
            for att, sc in ranked:
                if province and att["province"] != province:
                    continue
                if category and att["category"] != category:
                    continue
                if min_rating and att.get("rating", 0) < min_rating:
                    continue
                filtered.append((att, sc))
                if len(filtered) >= top_k:
                    break

            return filtered[:top_k]

    def get_by_id(self, aid: int):
        return self._id_index.get(aid)

    def get_by_name(self, name: str):
        """按名称 O(1) 查找景点"""
        return self._name_index.get(name)

    def get_by_province(self, province: str) -> list:
        return self._province_index.get(province, [])

    def get_by_category(self, category: str) -> list:
        return self._category_index.get(category, [])

    def _precompute_pinyin(self):
        """预计算所有景点的拼音并缓存到磁盘"""
        if self._pinyin_cache:
            return

        cache_path = os.path.join(CACHE_DIR, "pinyin_cache.pkl")
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "rb") as f:
                    self._pinyin_cache = pickle.load(f)
                if len(self._pinyin_cache) == len(self.attractions):
                    logger.info("从缓存加载拼音 (%d 个)", len(self._pinyin_cache))
                    return
            except Exception:
                pass

        try:
            from pypinyin import pinyin, Style
            for a in self.attractions:
                name = a["name"]
                if name in self._pinyin_cache:
                    continue
                py = "".join([item[0] for item in pinyin(name, style=Style.NORMAL)]).lower()
                initials = "".join([item[0][0] for item in pinyin(name, style=Style.NORMAL)])
                self._pinyin_cache[name] = (py, initials)
            # 缓存到磁盘
            try:
                with open(cache_path, "wb") as f:
                    pickle.dump(self._pinyin_cache, f)
                logger.info("拼音预计算完成并缓存 (%d 个)", len(self._pinyin_cache))
            except Exception as e:
                logger.warning("拼音缓存写入失败: %s", e)
        except ImportError:
            logger.warning("pypinyin 未安装，拼音检索不可用")

    def fuzzy_search(self, query: str, top_k: int = 5) -> list:
        """拼音纠错 + 模糊匹配检索（含省份/城市拼音）"""
        query_lower = query.lower().replace(" ", "")
        exact_matches = [a for name, a in self._name_index.items()
                         if query_lower in name.lower()]
        if exact_matches:
            return [(a, 1.0) for a in exact_matches[:top_k]]

        try:
            from pypinyin import pinyin, Style
            self._precompute_pinyin()
            query_py = "".join([item[0] for item in pinyin(query, style=Style.NORMAL)]).lower()

            scored = []
            for a in self.attractions:
                name_py, name_initials = self._pinyin_cache.get(a["name"], ("", ""))
                if not name_py:
                    continue

                prov_py = "".join([item[0] for item in pinyin(a["province"], style=Style.NORMAL)]).lower()
                city_py = ""
                if a.get("city"):
                    city_py = "".join([item[0] for item in pinyin(a["city"], style=Style.NORMAL)]).lower()

                hit = False
                if query_py in name_py or name_py in query_py:
                    hit = True
                elif query_py in prov_py or prov_py in query_py:
                    hit = True
                elif city_py and (query_py in city_py or city_py in query_py):
                    hit = True
                elif query_py in name_initials:
                    hit = True

                if hit:
                    common_len = len(set(query_py) & set(name_py + prov_py + city_py))
                    score = common_len / max(len(query_py), 1)
                    if score > 0.3:
                        scored.append((score, a))

            scored.sort(key=lambda x: -x[0])
            if scored:
                return [(a, s) for s, a in scored[:top_k]]
        except ImportError:
            pass

        return []

    def get_provinces(self) -> list:
        return sorted(set(a["province"] for a in self.attractions))

    def get_categories(self) -> list:
        return sorted(set(a["category"] for a in self.attractions))

    def random_attractions(self, n: int = 5) -> list:
        import random
        return random.sample(self.attractions, min(n, len(self.attractions)))

    def get_stats(self) -> dict:
        return {
            "total": len(self.attractions),
            "provinces": len(self.get_provinces()),
            "categories": self.get_categories(),
        }

    def get_related(self, att: dict, top_n: int = 4) -> list:
        """获取关联景点（优先手工关联 related_ids，再按省份/分类回退）"""
        related = []
        # 优先手工策划的关联
        for rid in att.get("related_ids", []):
            r = self.get_by_id(rid)
            if r and r not in related:
                related.append(r)
                if len(related) >= top_n:
                    return related

        # 回退：同省份 + 同分类
        same_province = [a for a in self._province_index.get(att["province"], [])
                         if a["id"] != att["id"] and a not in related]
        same_category = [a for a in self._category_index.get(att["category"], [])
                         if a["id"] != att["id"] and a not in related and a not in same_province]

        related.extend((same_province[:3] + same_category[:3])[:top_n - len(related)])
        return related
