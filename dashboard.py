import streamlit as st
import pandas as pd
import warnings

# Check and import plotly
try:
    import plotly.express as px
    import plotly.graph_objects as go
except ImportError:
    st.error("""
        Plotly not found. Installing required packages...
        Please wait a moment and refresh the page.
        If the error persists, run: pip install plotly plotly-express
    """)
    import subprocess
    subprocess.check_call(["pip", "install", "plotly", "plotly-express"])
    st.stop()

# Mengabaikan peringatan yang tidak relevan
warnings.filterwarnings('ignore')

# Konfigurasi halaman Streamlit
st.set_page_config(
    page_title="Dashboard Analisis Truk Air Bersih",
    page_icon="💧",
    layout="wide"
)

# Kustomisasi CSS untuk tampilan modern
st.markdown("""
<style>
    .main-header { font-size: 2.5rem; color: #1E90FF; text-align: center; margin-bottom: 2rem; font-weight: bold; }
    .metric-card { padding: 1.5rem; border-radius: 15px; color: white; text-align: center; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
    .metric-income { background: linear-gradient(135deg, #28a745 0%, #218838 100%); }
    .metric-expense { background: linear-gradient(135deg, #dc3545 0%, #c82333 100%); }
    .metric-water { background: linear-gradient(135deg, #17a2b8 0%, #138496 100%); }
    .metric-armada { background: linear-gradient(135deg, #ffc107 0%, #e0a800 100%); }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_keuangan_data():
    """Memuat dan membersihkan data keuangan dengan metode yang lebih tangguh."""
    try:
        # Baca CSV dengan memperhatikan kolom yang tergabung
        df = pd.read_csv('keuangan_data.csv', sep=',')
        # Lowercase dan strip whitespace dari nama kolom
        df.columns = df.columns.str.strip().str.lower()
        
        # Pemetaan nama kolom
        column_mapping = {
            'plat nomor': 'nopol',
            'volume (l)': 'jumlahair',
            'jumlah air': 'jumlahair'
        }
        
        # Terapkan pemetaan kolom
        df = df.rename(columns=column_mapping)
        
        # Konversi tanggal
        df['tanggal'] = pd.to_datetime(df['tanggal'], format='%d/%m/%Y', errors='coerce')
        df.dropna(subset=['tanggal'], inplace=True)
        
        # Bersihkan kolom numerik
        for col in ['pemasukan', 'pengeluaran', 'jumlahair']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace('Rp', '').str.replace('.', '')
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Bersihkan kolom kategorikal
        for col in ['nopol', 'sopir', 'jenis transaksi']:
            if col in df.columns:
                df[col] = df[col].fillna('Tidak Diketahui')
        
        df['Nama_Bulan'] = df['tanggal'].dt.strftime('%Y-%m (%B)')
        return df
    except Exception as e:
        st.error(f"Gagal memuat keuangan_data.csv: {str(e)}")
        st.write("Struktur data yang ditemukan:", df.columns.tolist())
        return None

@st.cache_data
def load_gps_data():
    """Memuat dan membersihkan data GPS."""
    try:
        df = pd.read_csv('data_gps.csv', sep=',')
        df.columns = df.columns.str.strip().str.lower()
        
        # Perbaikan nama kolom dan validasi data
        if 'nama lokasi' in df.columns:
            df = df.rename(columns={'nama lokasi': 'lokasi'})
        
        # Validasi koordinat
        for col in ['latitude', 'longitude']:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')
        
        df = df.dropna(subset=['latitude', 'longitude'])
        df = df[(df['latitude'].between(-90, 90)) & (df['longitude'].between(-180, 180))]
        
        if df.empty:
            st.error("Tidak ada data GPS valid yang dapat ditampilkan")
            return None
            
        return df
    except Exception as e:
        st.error(f"Gagal memuat data_gps.csv: {str(e)}")
        return None

def main():
    st.markdown('<h1 class="main-header">💧 Dashboard Analisis Truk Air Bersih</h1>', unsafe_allow_html=True)
    
    df_keuangan = load_keuangan_data()
    df_gps = load_gps_data()

    if df_keuangan is None or df_gps is None:
        st.stop()

    st.sidebar.title("⚙️ Filter Data")
    all_months_option = "Semua Bulan"
    bulan_list = [all_months_option] + sorted(df_keuangan['Nama_Bulan'].unique())
    selected_month = st.sidebar.selectbox("Pilih Bulan", bulan_list)

    if selected_month == all_months_option:
        filtered_df = df_keuangan
    else:
        filtered_df = df_keuangan[df_keuangan['Nama_Bulan'] == selected_month]
    st.sidebar.info(f"Menampilkan **{len(filtered_df)}** dari **{len(df_keuangan)}** total transaksi.")

    st.subheader("📈 Metrik Utama Berdasarkan Filter")
    total_pemasukan = filtered_df['pemasukan'].sum()
    total_pengeluaran = filtered_df['pengeluaran'].sum()
    total_air = filtered_df['jumlahair'].sum()
    total_armada = filtered_df[filtered_df['nopol'] != 'Tidak Diketahui']['nopol'].nunique()
    
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    m_col1.markdown(f'<div class="metric-card metric-income"><h5>Total Pemasukan</h5><h3>Rp {total_pemasukan:,.0f}</h3></div>', unsafe_allow_html=True)
    m_col2.markdown(f'<div class="metric-card metric-expense"><h5>Total Pengeluaran</h5><h3>Rp {total_pengeluaran:,.0f}</h3></div>', unsafe_allow_html=True)
    m_col3.markdown(f'<div class="metric-card metric-water"><h5>Total Air Terkirim</h5><h3>{total_air:,.0f} Liter</h3></div>', unsafe_allow_html=True)
    m_col4.markdown(f'<div class="metric-card metric-armada"><h5>Armada Beroperasi</h5><h3>{total_armada} Truk</h3></div>', unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    st.subheader("1. Rekapitulasi Keuangan & Pengiriman Air")
    col1, col2 = st.columns(2)
    with col1:
        keuangan_bulanan = df_keuangan.groupby('Nama_Bulan')[['pemasukan', 'pengeluaran']].sum().reset_index()
        fig1 = go.Figure()
        fig1.add_trace(go.Bar(x=keuangan_bulanan['Nama_Bulan'], y=keuangan_bulanan['pemasukan'], name='Pemasukan', marker_color='green'))
        fig1.add_trace(go.Bar(x=keuangan_bulanan['Nama_Bulan'], y=keuangan_bulanan['pengeluaran'], name='Pengeluaran', marker_color='red'))
        fig1.update_layout(title_text='Grafik Keuangan per Bulan', barmode='group')
        st.plotly_chart(fig1, use_container_width=True)
    with col2:
        pengiriman_bulanan = df_keuangan.groupby('Nama_Bulan')['jumlahair'].sum().reset_index()
        fig2 = px.line(pengiriman_bulanan, x='Nama_Bulan', y='jumlahair', title='Volume Air Terkirim per Bulan', markers=True)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    st.subheader("2. Peta Sebaran Titik Lokasi Pengiriman")
    if df_gps is not None and not df_gps.empty:
        st.info("Peta menunjukkan lokasi pengiriman air. Gunakan mouse untuk zoom dan pan.")
        
        center_lat = df_gps['latitude'].mean()
        center_lon = df_gps['longitude'].mean()
        
        fig_map = go.Figure(go.Scattermapbox(
            lat=df_gps['latitude'],
            lon=df_gps['longitude'],
            mode='markers',
            marker=go.scattermapbox.Marker(size=12, color='red'),
            text=df_gps['lokasi'],
        ))

        fig_map.update_layout(
            title='Sebaran Lokasi Pengiriman',
            height=500,
            mapbox=dict(
                style='open-street-map',  # Using OpenStreetMap
                center=dict(lat=center_lat, lon=center_lon),
                zoom=11
            ),
            margin=dict(r=0, t=30, l=0, b=0),
        )
        
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.warning("Tidak ada data GPS yang dapat ditampilkan")

    st.markdown("<hr>", unsafe_allow_html=True)
    
    st.subheader("3. Analisis Kinerja")
    col3, col4 = st.columns(2)
    with col3:
        st.write("#### Kinerja Armada")
        kinerja_armada = df_keuangan[df_keuangan['nopol'] != 'Tidak Diketahui'].groupby('nopol').agg(Total_Air_Terangkut=('jumlahair', 'sum'), Total_Biaya_Operasional=('pengeluaran', 'sum'), Frekuensi_Penggunaan=('tanggal', 'count')).reset_index()
        if not kinerja_armada.empty:
            fig4 = px.bar(kinerja_armada, x='nopol', y=['Total_Air_Terangkut', 'Total_Biaya_Operasional', 'Frekuensi_Penggunaan'], title='Perbandingan Kinerja per Armada', barmode='group')
            st.plotly_chart(fig4, use_container_width=True)
    with col4:
        st.write("#### Frekuensi Kerja Sopir")
        kinerja_sopir = filtered_df[filtered_df['sopir'] != 'Tidak Diketahui'].groupby('sopir').agg(Jumlah_Trip=('tanggal', 'count'), Total_Air_Dikirim=('jumlahair', 'sum')).reset_index().sort_values(by='Jumlah_Trip', ascending=False)
        if not kinerja_sopir.empty:
            fig5 = px.bar(kinerja_sopir, x='Jumlah_Trip', y='sopir', orientation='h', title=f'Frekuensi Kerja Sopir (Periode Terfilter)', text='Jumlah_Trip')
            st.plotly_chart(fig5, use_container_width=True)

if __name__ == "__main__":
    main()