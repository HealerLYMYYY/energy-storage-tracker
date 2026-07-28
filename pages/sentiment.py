"""舆情监控页"""
import streamlit as st
from utils.data_manager import get_competitors


def show_sentiment():
    st.title("📰 行业舆情监控")
    st.caption("全行业关键词：光伏 · 储能 · 锂电池 · 新能源 · AIDC · 招标 · 中标 · 项目公告")

    competitors = get_competitors()

    # 公司舆情卡片
    st.subheader("🔍 竞对公司舆情")
    cols = st.columns(3)
    for i, c in enumerate(competitors):
        with cols[i % 3]:
            st.markdown(f"""
            <div style="border:1px solid #e5e7eb;border-radius:10px;padding:14px;margin-bottom:10px;
                        border-left:4px solid {c['color']}">
                <div style="font-weight:600;font-size:0.9rem">{c['name']}</div>
                <div style="font-size:0.7rem;color:#6b7280;margin:4px 0">{c['keywords'][:60]}...</div>
            </div>""", unsafe_allow_html=True)
            st.link_button(f"🔗 搜索 {c['name']}",
                           f"https://news.google.com/search?q={c['name']}+储能+光伏&hl=zh-CN",
                           use_container_width=True, key=f"sent_{c['cid']}")

    st.divider()

    # 行业舆情搜索入口
    st.subheader("🌐 行业舆情搜索")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.link_button("🔗 Google News - 储能行业",
                       "https://news.google.com/search?q=储能+光伏+锂电池+行业&hl=zh-CN",
                       use_container_width=True)
    with col_b:
        st.link_button("🔗 财联社 - 储能",
                       "https://www.cls.cn/searchPage?keyword=储能&type=all",
                       use_container_width=True)
    with col_c:
        st.link_button("🔗 东方财富公告",
                       "https://stock.eastmoney.com/a/czgg.html",
                       use_container_width=True)

    col_d, col_e = st.columns(2)
    with col_d:
        st.link_button("🔗 界面新闻 - 新能源",
                       "https://www.jiemian.com/lists/280.html",
                       use_container_width=True)
    with col_e:
        st.link_button("🔗 百度搜索 - 储能招标",
                       "https://www.baidu.com/s?wd=储能+招标+中标+2025",
                       use_container_width=True)

    st.info("💡 舆情监控功能通过外部搜索链接实现。如需内置 RSS 聚合和实时舆情抓取，可以配置 NewsAPI 或 Google News RSS 接口。")
