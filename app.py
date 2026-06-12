import os
import pandas as pd
import plotly.express as px
import streamlit as st

# 1. 網頁基本頁面設定
st.set_page_config(
    page_title="全台零售業展店數據決策系統", page_icon="📍", layout="wide"
)

st.title("📍 全台零售業展店與商圈數據決策系統 (真實官方數據商用版)")
st.markdown(
    "本系統即時加載**財政部綜所稅各村里結算大數據**與**內政部人口指標**，進行全台商圈展店潛力精準分析。"
)
st.write("---")


# 2. 自動加載真實 CSV 數據庫邏輯
@st.cache_data
def load_real_data():
    csv_file = "real_taiwan_income.csv"

    # 防呆機制：如果找不到真實檔案，會顯示警告
    if not os.path.exists(csv_file):
        st.error(f"❌ 系統找不到真實數據檔：{csv_file}，請確認檔案是否已上傳至同一個資料夾。")
        return pd.DataFrame()

    # 讀取真實數據
    df_data = pd.read_csv(csv_file, encoding="utf-8")
    return df_data


df = load_real_data()

if not df.empty:
    # 3. 左側側邊欄：互動式控制面板
    st.sidebar.header("🎛️ 展店市場篩選條件")

    # 控制面板全面採用「真實所得中位數」作為基本盤篩選
    min_median_income = st.sidebar.slider(
        "最低里居民【所得中位數】(萬元)",
        min_value=int(df["所得中位數_萬元"].min()),
        max_value=int(df["所得中位數_萬元"].max()),
        value=75,
        step=5,
    )

    min_age_ratio = st.sidebar.slider(
        "目標核心客群佔比門檻 (%)",
        min_value=20,
        max_value=40,
        value=25,
        step=1,
    )

    city_list = sorted(df["縣市"].unique())
    selected_cities = st.sidebar.multiselect(
        "選擇評估縣市", city_list, default=city_list
    )

    # 4. 數據篩選與精準權重計分邏輯 (商用演算法)
    filtered_df = df[
        (df["所得中位數_萬元"] >= min_median_income)
        & (df["目標年齡層佔比_百分比"] >= min_age_ratio)
        & (df["縣市"].isin(selected_cities))
    ]

    # 調整展店潛力總分演算法：中位數佔40%、平均數佔20%、年齡佔比佔40%
    filtered_df["展店潛力總分"] = (
        (filtered_df["所得中位數_萬元"] * 0.4)
        + (filtered_df["所得平均數_萬元"] * 0.2)
        + (filtered_df["目標年齡層佔比_百分比"] * 4.0)
    ).round(1)
    filtered_df = filtered_df.sort_values(by="展店潛力總分", ascending=False)

    # 5. 前端網頁排版 (左右雙欄視覺化呈現)
    col1, col2 = st.columns([6, 4])

    with col1:
        st.subheader("🗺️ 全台商圈展店潛力地理分布熱點")
        if not filtered_df.empty:
            # 繪製全台 GIS 互動式地圖
            fig = px.scatter_mapbox(
                filtered_df,
                lat="latitude",
                lon="longitude",
                hover_name="附近核心商場/商圈",
                hover_data=[
                    "縣市",
                    "鄉鎮市區",
                    "村里",
                    "所得中位數_萬元",
                    "所得平均數_萬元",
                    "展店潛力總分",
                ],
                color="展店潛力總分",
                size="所得中位數_萬元",
                color_continuous_scale=px.colors.cyclical.IceFire,
                size_max=22,
                zoom=7,
                mapbox_style="carto-positron",
                height=580,
            )
            fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("⚠️ 當前篩選條件過於嚴格，地圖無符合之商圈。請放寬左側篩選標準。")

    with col2:
        st.subheader("🏆 最佳展店/進駐商場推薦排名")
        if not filtered_df.empty:
            display_df = filtered_df[
                [
                    "附近核心商場/商圈",
                    "縣市",
                    "所得中位數_萬元",
                    "所得平均數_萬元",
                    "展店潛力總分",
                ]
            ].reset_index(drop=True)
            display_df.columns = [
                "核心商場/商圈",
                "縣市",
                "所得中位數",
                "所得平均數",
                "潛力總分",
            ]
            st.dataframe(display_df, use_container_width=True, height=540)
        else:
            st.info("暫無推薦資料")

    st.write("---")
    st.subheader("📊 篩選商圈詳細數據明細")
    st.write(
        "本表呈現真實官方統計。中位數貼近在地民情基本盤，平均數反應高消費力極端值，兩者差距可做為定價策略參考。"
    )
    st.dataframe(filtered_df, use_container_width=True)
