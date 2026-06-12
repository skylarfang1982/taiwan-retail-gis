import pandas as pd
import plotly.express as px
import streamlit as st

# 1. 網頁基本頁面設定
st.set_page_config(
    page_title="全台零售業展店數據決策系統", page_icon="📍", layout="wide"
)

st.title("📍 全台零售業展店與商圈數據決策系統")
st.markdown(
    "本系統整合**財政部村里所得大數據**、**內政部人口結構**與**全台核心商場地理資訊**，協助評估最佳展店位址。"
)
st.write("---")


# 2. 載入核心整合數據 (包含經緯度、所得、年齡佔比、鄰近商場)
@st.cache_data
def load_market_data():
    data = {
        "縣市": [
            "新竹市",
            "新竹市",
            "台北市",
            "台北市",
            "新竹縣",
            "台南市",
            "高雄市",
            "台中市",
            "台北市",
            "新北市",
        ],
        "鄉鎮市區": [
            "東區",
            "東區",
            "大安區",
            "信義區",
            "竹北市",
            "善化區",
            "鼓山區",
            "西屯區",
            "中山區",
            "板橋區",
        ],
        "村里": [
            "關新里",
            "龍山里",
            "民炤里",
            "安康里",
            "鹿場里",
            "蓮潭里",
            "龍水里",
            "惠來里",
            "成功里",
            "福丘里",
        ],
        "所得平均數_萬元": [
            301.2,
            210.5,
            182.4,
            175.2,
            195.1,
            168.9,
            145.6,
            152.3,
            138.2,
            132.5,
        ],
        "目標年齡層佔比_百分比": [
            32.5,
            28.4,
            35.1,
            33.8,
            31.2,
            26.5,
            29.8,
            34.2,
            30.5,
            31.9,
        ],
        "附近核心商場/商圈": [
            "新竹科學園區商圈",
            "Costco新竹店周邊",
            "遠東SOGO復興館",
            "台北信義新天地/微風信義",
            "遠東百貨竹北店",
            "南科工程師高級聚落",
            "高雄美術館特區",
            "台中新光三越/大遠百",
            "新光三越台北南西店",
            "板橋大遠百/環球購物中心",
        ],
        "latitude": [
            24.7836,
            24.7912,
            25.0392,
            25.0358,
            24.8225,
            23.1254,
            22.6592,
            24.1645,
            25.0515,
            25.0135,
        ],
        "longitude": [
            121.0182,
            121.0042,
            121.5432,
            121.5668,
            121.0142,
            120.2982,
            120.2845,
            120.6432,
            121.5215,
            121.4654,
        ],
    }
    return pd.DataFrame(data)


df = load_market_data()

# 3. 左側側邊欄：互動式控制面板
st.sidebar.header("🎛️ 展店市場篩選條件")
min_income = st.sidebar.slider(
    "最低里居民平均年所得 (萬元)",
    min_value=100,
    max_value=350,
    value=130,
    step=10,
)
min_age_ratio = st.sidebar.slider(
    "目標核心客群佔比門檻 (%)",
    min_value=20,
    max_value=40,
    value=28,
    step=1,
)
all_cities = df["縣市"].unique()
selected_cities = st.sidebar.multiselect("選擇評估縣市", all_cities, default=all_cities)

# 4. 數據篩選與權重計分邏輯
filtered_df = df[
    (df["所得平均數_萬元"] >= min_income)
    & (df["目標年齡層佔比_百分比"] >= min_age_ratio)
    & (df["縣市"].isin(selected_cities))
]

filtered_df["展店潛力總分"] = (
    (filtered_df["所得平均數_萬元"] * 0.6)
    + (filtered_df["目標年齡層佔比_百分比"] * 4.0)
).round(1)
filtered_df = filtered_df.sort_values(by="展店潛力總分", ascending=False)

# 5. 前端網頁排版 (左右雙欄)
col1, col2 = st.columns([6, 4])

with col1:
    st.subheader("🗺️ 全台商圈展店潛力地理分布熱點")
    if not filtered_df.empty:
        # 繪製 GIS 互動式地圖
        fig = px.scatter_mapbox(
            filtered_df,
            lat="latitude",
            lon="longitude",
            hover_name="附近核心商場/商圈",
            hover_data=["縣市", "鄉鎮市區", "村里", "所得平均數_萬元", "展店潛力總分"],
            color="展店潛力總分",
            size="所得平均數_萬元",
            color_continuous_scale=px.colors.cyclical.IceFire,
            size_max=25,
            zoom=7,
            mapbox_style="carto-positron",
            height=550,
        )
        fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("⚠️ 當前篩選條件過於嚴格，地圖無符合之商圈。")

with col2:
    st.subheader("🏆 最佳展店/進駐商場推薦排名")
    if not filtered_df.empty:
        display_df = filtered_df[
            [
                "附近核心商場/商圈",
                "縣市",
                "鄉鎮市區",
                "所得平均數_萬元",
                "展店潛力總分",
            ]
        ].reset_index(drop=True)
        st.dataframe(display_df, use_container_width=True, height=510)
    else:
        st.info("暫無推薦資料")

st.write("---")
st.subheader("📊 篩選商圈詳細數據明細")
st.dataframe(filtered_df, use_container_width=True)
