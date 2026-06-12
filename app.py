import os
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="全台零售業展店數據決策系統", page_icon="📍", layout="wide"
)

st.title("📍 全台零售業展店與商圈數據決策系統-Skylar")
st.markdown(
    "本系統整合**財政部鄉鎮市區綜所稅中位數大數據**與**真實核心商場分布**，提供高層次展店戰略評估。"
)
st.write("---")


# 改讀取全新命名的 CSV 檔
@st.cache_data
def load_real_data():
    csv_file = "taiwan_district_mall.csv"  # 確保與改名後的檔案一致

    if not os.path.exists(csv_file):
        st.warning("⚠️ 數據庫同步中，請稍候...")
        return pd.DataFrame()

    try:
        df_data = pd.read_csv(csv_file, encoding="utf-8")
        return df_data
    except Exception as e:
        st.error(f"讀取 CSV 檔案時發生錯誤: {e}")
        return pd.DataFrame()


df = load_real_data()

if df.empty:
    st.info("💡 請確認對應的 CSV 檔案是否已成功生成並同步。")
else:
    # 控制面板
    st.sidebar.header("🎛️ 展店市場篩選條件")

    min_income = float(df["所得中位數_萬元"].min())
    max_income = float(df["所得中位數_萬元"].max())

    min_median_income = st.sidebar.slider(
        "最低居民【所得中位數】(萬元)",
        min_value=int(min_income),
        max_value=int(max_income),
        value=70,
        step=5,
    )

    min_age_ratio = st.sidebar.slider(
        "目標核心客群佔比門檻 (%)",
        min_value=20,
        max_value=40,
        value=24,
        step=1,
    )

    city_list = sorted(df["縣市"].unique())
    selected_cities = st.sidebar.multiselect(
        "選擇評估縣市", city_list, default=city_list
    )

    # 數據篩選
    filtered_df = df[
        (df["所得中位數_萬元"] >= min_median_income)
        & (df["目標年齡層佔比_百分比"] >= min_age_ratio)
        & (df["縣市"].isin(selected_cities))
    ]

    filtered_df["展店潛力總分"] = (
        (filtered_df["所得中位數_萬元"] * 0.4)
        + (filtered_df["附近核心商場/商圈"].get("所得平均數_萬元", 100) * 0.2)
        if "所得平均數_萬元" in filtered_df.columns
        else (filtered_df["所得中位數_萬元"] * 0.6)
    ) + (filtered_df["目標年齡層佔比_百分比"] * 4.0)

    if not filtered_df.empty:
        filtered_df["展店潛力總分"] = filtered_df["展店潛力總分"].round(1)

    filtered_df = filtered_df.sort_values(by="展店潛力總分", ascending=False)

    col1, col2 = st.columns([6, 4])

    with col1:
        st.subheader("🗺️ 全台商圈核心商場地理分布熱點")
        if not filtered_df.empty:
            fig = px.scatter_mapbox(
                filtered_df,
                lat="latitude",
                lon="longitude",
                hover_name="附近核心商場/商圈",
                hover_data=["縣市", "鄉鎮市區", "所得中位數_萬元", "展店潛力總分"],
                color="展店潛力總分",
                size="所得中位數_萬元",
                color_continuous_scale=px.colors.cyclical.IceFire,
                size_max=18,
                zoom=7,
                mapbox_style="carto-positron",
                height=580,
            )
            fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("⚠️ 沒有符合當前篩選條件的行政區。")

    with col2:
        st.subheader("🏆 最佳展店/進駐商場推薦排名")
        if not filtered_df.empty:
            display_df = filtered_df[
                ["附近核心商場/商圈", "縣市", "鄉鎮市區", "所得中位數_萬元", "展店潛力總分"]
            ].reset_index(drop=True)
            display_df.columns = [
                "主要進駐商場 / 商圈",
                "縣市",
                "行政區",
                "所得中位數(萬)",
                "潛力總分",
            ]
            st.dataframe(display_df, use_container_width=True, height=540)
        else:
            st.info("暫無推薦資料")

    st.write("---")
    st.subheader("📊 篩選行政區商圈詳細數據明細")
    st.dataframe(filtered_df, use_container_width=True)
