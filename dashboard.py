import streamlit as st
import pandas as pd
import plotly.express as px

# KONFIGURASI HALAMAN
st.set_page_config(layout="wide", page_title="Monitoring Bokori", page_icon=" ")

# LOAD CSS
try:
    with open("style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    pass

# FUNGSI LOAD DATA (Membaca Multi-Sheet)
# Atur waktu pembaruan data (TTL) dalam detik, misalnya 900 detik = 15 menit
CACHE_TTL = 300 
INTERVAL_MENIT = CACHE_TTL // 60

@st.cache_data(ttl=CACHE_TTL)
def load_data():
    SHEET_ID = "1AoWGWWmTzLCgsEJni8a5BjsWHlLJJe3K924DiKAokv4"
    
    url_rekon = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Rekon+Gaji"
    url_ppnpn = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=PPNPN"
    url_skpp  = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=SKPP"
    
    try:
        df_rekon = pd.read_csv(url_rekon)
        df_ppnpn = pd.read_csv(url_ppnpn)
        df_skpp  = pd.read_csv(url_skpp)
        return df_rekon, df_ppnpn, df_skpp, True
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), False

# Memuat data
df_rekon, df_ppnpn, df_skpp, is_connected = load_data()

# FITUR NOTIFIKASI POP-UP (TOAST)
if "notifikasi_sukses" not in st.session_state:
    if is_connected:
        st.toast('Berhasil terhubung ke Google Sheets!', icon='🎉')
        st.session_state.notifikasi_sukses = True
    else:
        st.toast('Gagal menarik data dari Google Sheets.', icon='⚠️')

# SIDEBAR
with st.sidebar:
    # 1. BUAT KOLOM UNTUK MENENGAHKAN LOGO
    # Rasio [1, 1.5, 1] artinya kolom tengah lebih lebar sedikit
    kol_kiri, kol_tengah, kol_kanan = st.columns([1, 1.5, 1])
    
    with kol_tengah:
        try:
            st.image("LOGO KPPN KENDARI.png", use_container_width=True)
        except Exception:
            st.warning("Logo tidak ditemukan. Cek nama/lokasi file.")

    st.markdown("<h3 style='text-align: center; color: #283593; margin-top: 5px;'>MONITORING BOKORI</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 12px; color: gray; margin-top:-15px;'>KPPN Kendari</p>", unsafe_allow_html=True)

    # Gunakan variabel menu_utama
    menu = st.radio("menu_utama", ["OVERVIEW", "REKON GAJIWEB", "PPNPN", "SKPP"], index=0)
    
    st.write("---")
    st.markdown('<div style="text-align:center; padding: 10px; background-color: #e8f5e9; border-radius: 25px; color: #2e7d32; font-size: 11px; font-weight: bold;">STATUS: TERHUBUNG</div>', unsafe_allow_html=True)

# HALAMAN OVERVIEW
if menu == "OVERVIEW":
    st.markdown('<h1>OVERVIEW</h1>', unsafe_allow_html=True)
    st.markdown(f'<p class="interval-text">Interval update data setiap {INTERVAL_MENIT} menit</p>', unsafe_allow_html=True)
    
    if not is_connected:
        st.error("Koneksi terputus. Silakan periksa link Google Sheets atau internet anda.")
        st.stop()

    # RINGKASAN VOLUME DATA
    m1, m2, m3, m4 = st.columns(4)
    
    with m1:
        # Mengambil data dari ketiga sheet
        sat_asn = df_rekon['Satuan Kerja'].dropna() if 'Satuan Kerja' in df_rekon.columns else pd.Series(dtype='str')
        sat_ppn = df_ppnpn['Kode Satker'].dropna() if 'Kode Satker' in df_ppnpn.columns else pd.Series(dtype='str')
        sat_skp = df_skpp['Kode Satker'].dropna() if 'Kode Satker' in df_skpp.columns else pd.Series(dtype='str')
        
        # Menumpuk ketiganya jadi satu daftar panjang
        all_satker = pd.concat([sat_asn, sat_ppn, sat_skp])
        
        # MEMOTONG TEKS: Hanya mengambil kode (bagian depan sebelum '-')
        kode_saja = all_satker.astype(str).str.split('-').str[0].str.strip()
        
        # Menghitung jumlah kode unik
        total_s = kode_saja.nunique()
        
        # Dibungkus container agar CSS [data-testid="stMetric"] bekerja maksimal
        with st.container():
            st.metric("Total Satker", f"{total_s}")

    with m2:
        with st.container():
            st.metric("VOLUME REKON GAJIWEB", f"{len(df_rekon):,}".replace(',', '.'))

    with m3:
        with st.container():
            st.metric("VOLUME REKON GAJI PPNPN", f"{len(df_ppnpn):,}".replace(',', '.'))

    with m4:
        with st.container():
            st.metric("VOLUME SKPP", f"{len(df_skpp):,}".replace(',', '.'))

    st.markdown("<div style='margin-bottom: 30px;'></div>", unsafe_allow_html=True)

    st.write("")

    # ANALISIS TREN & STATUS
    c1, c2 = st.columns([1.6, 1])

    with c1:
            st.markdown('<h3 style="color:#283593; font-size:18px; margin-bottom:10px;">Perbandingan Aktivitas Bulanan</h3>', unsafe_allow_html=True)
            try:
                # 1. FUNGSI AMBIL DATA WAKTU
                def ambil_data_timestamp(df, nama_sumber):
                    col_waktu = None
                    for col in df.columns:
                        if 'timestamp' in str(col).lower() or 'waktu' in str(col).lower():
                            col_waktu = col
                            break
                    if col_waktu:
                        temp = df[[col_waktu]].dropna().copy()
                        temp['Waktu Baku'] = pd.to_datetime(temp[col_waktu], errors='coerce', dayfirst=True)
                        temp = temp.dropna(subset=['Waktu Baku']) 
                        
                        bulan_indo = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'Mei', 6: 'Jun',
                                      7: 'Jul', 8: 'Agu', 9: 'Sep', 10: 'Okt', 11: 'Nov', 12: 'Des'}
                        temp['Bulan Tampil'] = temp['Waktu Baku'].dt.month.map(bulan_indo) + " " + temp['Waktu Baku'].dt.year.astype(str)
                        temp['Sumber'] = nama_sumber
                        return temp[['Bulan Tampil', 'Sumber', 'Waktu Baku']]
                    return pd.DataFrame(columns=['Bulan Tampil', 'Sumber', 'Waktu Baku'])

                b1 = ambil_data_timestamp(df_rekon, 'ASN')
                b2 = ambil_data_timestamp(df_ppnpn, 'PPNPN')
                b3 = ambil_data_timestamp(df_skpp, 'SKPP')

                df_all_bulan = pd.concat([b1, b2, b3])

                # Cari tahun berjalan (Misal: 2026)
                tahun_berjalan = "2026"
                if not df_all_bulan.empty and not pd.isna(df_all_bulan['Waktu Baku'].dt.year.max()):
                    tahun_berjalan = str(int(df_all_bulan['Waktu Baku'].dt.year.max()))

                bulan_list = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des']
                kerangka_bulan = [f"{b} {tahun_berjalan}" for b in bulan_list]

                df_kerangka = pd.MultiIndex.from_product([kerangka_bulan, ['ASN', 'PPNPN', 'SKPP']], names=['Bulan Tampil', 'Loket Layanan']).to_frame(index=False)
                df_kerangka['Jumlah'] = 0

                if not df_all_bulan.empty:
                    df_trend = df_all_bulan.groupby(['Bulan Tampil', 'Sumber']).size().reset_index(name='Jumlah_Asli')
                    df_trend.rename(columns={'Sumber': 'Loket Layanan'}, inplace=True)
                    
                    df_final = pd.merge(df_kerangka, df_trend, on=['Bulan Tampil', 'Loket Layanan'], how='left')
                    df_final['Jumlah'] = df_final['Jumlah_Asli'].fillna(0).astype(int)
                else:
                    df_final = df_kerangka

                # 3. MENGGAMBAR GRAFIK
                fig_line = px.line(df_final, x='Bulan Tampil', y='Jumlah', color='Loket Layanan', 
                                   markers=True, line_shape="spline", 
                                   color_discrete_map={"ASN": "#283593", "PPNPN": "#c62828", "SKPP": "#00897b"})
                
                fig_line.update_traces(line=dict(width=3), marker=dict(size=8))
                
                fig_line.update_layout(
                    xaxis=dict(
                        title=dict(text="Periode Bulan", standoff=30), 
                        type="category", 
                        categoryorder="array",           
                        categoryarray=kerangka_bulan,    
                        tickangle=-45,                   
                        showgrid=True,
                        gridcolor='rgba(200, 200, 200, 0.2)'
                    ),
                    yaxis=dict(
                        title=dict(text="Volume Pengajuan", standoff=25),
                        showgrid=True,
                        gridcolor='rgba(200, 200, 200, 0.2)',
                        rangemode="tozero",
                        zeroline=False
                    ),
                    hovermode="x unified", 
                    plot_bgcolor='rgba(0,0,0,0)', 
                    paper_bgcolor='rgba(0,0,0,0)', 
                    legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5), 
                    margin=dict(l=80, r=20, t=40, b=100), 
                    height=450 
                )
                
                st.plotly_chart(fig_line, use_container_width=True, theme=None)
            except Exception as e:
                st.error(f"Gagal memuat grafik tren: {str(e)}")
    with c2:
        st.markdown('<h3 style="color:#283593; font-size:18px; margin-bottom:10px;">Persentase Status Global</h3>', unsafe_allow_html=True)
        try:
            def ambil_status_pintar(df):
                for col in df.columns:
                    # Mengecek apakah ada kata 'STATUS' di dalam nama kolom
                    if 'STATUS' in str(col).upper():
                        # Jika ketemu (misal: 'status FO' atau 'Status ADK'), langsung ambil datanya!
                        return df[col].dropna().astype(str)
                # Jika benar-benar tidak ada kolom berbau status, kembalikan data kosong
                return pd.Series(dtype='str')

            # 2. Ambil data status dari 3 sheet 
            s1 = ambil_status_pintar(df_rekon)
            s2 = ambil_status_pintar(df_ppnpn)
            s3 = ambil_status_pintar(df_skpp)

            # 3. Gabungkan semua statusnya
            df_status_raw = pd.concat([s1, s2, s3])
            
            if not df_status_raw.empty:
                # FILTER : Hanya ambil status yang ada di data (Jumlah > 0)
                counts = df_status_raw.value_counts()
                df_status = counts[counts > 0].reset_index()
                df_status.columns = ['Status', 'Jumlah']
                
                total_data = df_status['Jumlah'].sum()

                # PALET WARNA DINAMIS: Otomatis dipasangkan ke status apa pun yang muncul
                # Urutan: Biru Tua, Merah, Kuning, Hijau, Ungu, Oranye, dst.
                palet_status = ["#283593", "#c62828", "#fbc02d", "#2e7d32", "#673ab7", "#fb8c00", "#00897b", "#78909c"]
                
                # Membuat mapping warna otomatis berdasarkan status yang ditemukan di data
                status_unik = df_status['Status'].unique()
                warna_map_dinamis = {stat: palet_status[i % len(palet_status)] for i, stat in enumerate(status_unik)}

                # Buat Grafik Donut
                fig_donut = px.pie(df_status, names='Status', values='Jumlah', hole=.55,
                                   color='Status', color_discrete_map=warna_map_dinamis)
                
                fig_donut.update_traces(
                    textinfo='percent', 
                    textposition='inside',
                    hoverinfo='label+value+percent',
                    marker=dict(line=dict(color='#FFFFFF', width=2.5)) 
                )
                
                fig_donut.update_layout(
                    annotations=[dict(text=f"Total<br><b>{total_data}</b>", x=0.5, y=0.5, font_size=16, showarrow=False, font=dict(color="#283593"))],
                    showlegend=False,
                    margin=dict(l=10, r=10, t=20, b=10), 
                    height=300,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)'
                )
                
                st.plotly_chart(fig_donut, use_container_width=True, theme=None)

                # LEGENDA MASTER DINAMIS 
                st.write("")
                legenda_html = '<div style="display: flex; justify-content: center; flex-wrap: wrap; gap: 15px; padding: 5px;">'
                for _, row in df_status.iterrows():
                    warna = warna_map_dinamis.get(row['Status'])
                    legenda_html += f'''
                        <div style="display: flex; align-items: center;">
                            <div style="width: 12px; height: 12px; background-color: {warna}; margin-right: 6px; border-radius: 2px;"></div> 
                            <span style="font-size:12px; font-weight:bold; color:#444;">{row['Status']}</span>
                        </div>'''
                legenda_html += '</div>'
                st.markdown(legenda_html, unsafe_allow_html=True)
                
            else:
                st.info("Belum ada data status di spreadsheet.")
        except Exception as e:
            st.error(f"Gagal memuat status: {str(e)}")

    # ANALISIS BERDASARKAN KATEGORI 
    st.write("")
    st.markdown('<h3 style="color:#283593; font-size:18px; margin-bottom:15px;">Proporsi Pengajuan Berdasarkan Kategori</h3>', unsafe_allow_html=True)

    # Peta Warna Standar 
    palet_warna = ["#283593", "#fbc02d", "#2e7d32", "#4e342e", "#c62828", "#673ab7", "#fb8c00", "#00897b", "#78909c"]
    
    # Fungsi untuk memproses data & warna secara sinkron
    def dapatkan_data_dan_warna(dfs):
        kategori_ditemukan = {} 
        hasil_grafik = []
        warna_idx = 0
        
        for df in dfs:
            col_target = None
            for col in df.columns:
                if any(x in col.lower() for x in ['jenis', 'pegawai', 'kategori']):
                    col_target = col
                    break
            
            if col_target:
                df_c = df[col_target].dropna().astype(str).str.strip().str.upper().value_counts().reset_index()
                df_c.columns = ['Kategori', 'Jumlah']
                df_c = df_c[~df_c['Kategori'].isin(['', 'NAN', 'NULL'])]
                
                # Daftarkan warna untuk kategori baru yang belum pernah muncul
                for kat in df_c['Kategori']:
                    if kat not in kategori_ditemukan:
                        kategori_ditemukan[kat] = palet_warna[warna_idx % len(palet_warna)]
                        warna_idx += 1
                hasil_grafik.append((df_c, col_target))
            else:
                hasil_grafik.append((None, None))
        
        return hasil_grafik, kategori_ditemukan

    # Eksekusi pemindaian
    list_df_hasil, master_color_map = dapatkan_data_dan_warna([df_rekon, df_ppnpn, df_skpp])

    # Tampilkan Legenda Master (Hanya yang ada isinya saja)
    if master_color_map:
        legend_html = '<div style="display: flex; justify-content: center; flex-wrap: wrap; gap: 15px; margin-bottom: 25px; padding: 10px; background-color: #f8f9fa; border-radius: 10px;">'
        for kat, warna in master_color_map.items():
            legend_html += f'''
                <div style="display: flex; align-items: center;">
                    <div style="width: 12px; height: 12px; background-color: {warna}; margin-right: 5px; border-radius: 2px;"></div> 
                    <span style="font-size:12px; font-weight:bold;">{kat}</span>
                </div>'''
        legend_html += '</div>'
        st.markdown(legend_html, unsafe_allow_html=True)

    # Tampilkan 3 Grafik
    k1, k2, k3 = st.columns(3)
    titles = ["Layanan REKON GAJI", "Layanan PPNPN", "Layanan SKPP"]
    cols = [k1, k2, k3]

    for i, (df_c, col_name) in enumerate(list_df_hasil):
        with cols[i]:
            if df_c is not None and not df_c.empty:
                fig = px.bar(df_c, x='Kategori', y='Jumlah', text='Jumlah',
                             title=f"<b>{titles[i]}</b>",
                             color='Kategori',
                             color_discrete_map=master_color_map)
                
                fig.update_traces(textposition='outside', textfont_size=11)
                fig.update_layout(
                    showlegend=False, title_x=0.5, height=300,
                    margin=dict(l=5, r=5, t=40, b=20),
                    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                    xaxis=dict(showgrid=False, tickfont_size=9, title=None),
                    yaxis=dict(showgrid=True, gridcolor='rgba(200,200,200,0.2)', showticklabels=False, title=None)
                )
                st.plotly_chart(fig, use_container_width=True, theme=None)
            else:
                st.info(f"Data {titles[i]} Kosong")

# HALAMAN REKON GAJI
elif menu == "REKON GAJIWEB":
    st.markdown('<h1 style="color:#283593;">REKON GAJIWEB (ASN, PPPK, TNI, POLRI)</h1>', unsafe_allow_html=True)
    st.markdown(f'<p class="interval-text">Interval update data setiap {INTERVAL_MENIT} menit</p>', unsafe_allow_html=True)
    
    # HILANGKAN FITUR DOWNLOAD EXCEL/CSV (Toolbar)
    st.markdown("""
        <style>
        [data-testid="stElementToolbar"] {
            display: none !important;
        }
        </style>
    """, unsafe_allow_html=True)

    if not df_rekon.empty:
        # 1. UBAH TYPE TIMESTAMP JADI DATE & SORT DATA TERBARU
        if 'Timestamp' in df_rekon.columns:
            df_rekon['Timestamp'] = pd.to_datetime(df_rekon['Timestamp'], errors='coerce', dayfirst=True)
            df_rekon = df_rekon.sort_values(by='Timestamp', ascending=False)

        # 2. PERSIAPAN DATA SATKER 
        # if 'Satuan Kerja' in df_rekon.columns:
        #     satker_split = df_rekon['Satuan Kerja'].astype(str).str.split('-', n=1, expand=True)
        #     if satker_split.shape[1] == 2:
        #         df_rekon['Kode Satker'] = satker_split[0].str.strip()
        #         df_rekon['Nama Satker'] = satker_split[1].str.strip()
        #     else:
        #         df_rekon['Kode Satker'] = df_rekon['Satuan Kerja']
        #         df_rekon['Nama Satker'] = df_rekon['Satuan Kerja']
                
        #     # Tabel Daftar Satker (Bagian Atas)
        #     st.markdown('<h3 style="color:#283593; font-size:18px;">Daftar Satker</h3>', unsafe_allow_html=True)
        #     df_satker_list = df_rekon[['Kode Satker', 'Nama Satker']].drop_duplicates().reset_index(drop=True)
        #     df_satker_list.index += 1 
        #     st.dataframe(df_satker_list, use_container_width=True, height=200) 
        # st.write("")

        # 3. SISTEM FILTER DINAMIS
        st.markdown('<h3 style="color:#283593; font-size:18px;">Filter Data Detail</h3>', unsafe_allow_html=True)
        cb1, cb2, cb3, cb4 = st.columns(4)
        
        # KEY unik agar tidak bentrok dengan menu lain yang mungkin punya filter serupa
        use_satker = cb1.checkbox("Filter Satker (Kode/Nama)", key="cb_satker_gaji")
        use_bulan = cb2.checkbox("Filter Bulan", key="cb_bulan_gaji")
        use_pegawai = cb3.checkbox("Filter Jenis Pegawai", key="cb_pegawai_gaji")
        use_status = cb4.checkbox("Filter Status ADK", key="cb_status_gaji")

        df_filtered = df_rekon.copy()
        in1, in2, in3, in4 = st.columns(4)
        
        # LOGIKA FILTER SATKER 
        if use_satker:
            with in1:
                search_satker = st.text_input("Ketik Kode/Nama Satker:", key="in_satker_gaji")
                if search_satker:
                    daftar_kolom_besar = [c.upper() for c in df_filtered.columns]
                    target_col = None
                    
                    # Cek prioritas kolom yang akan digeledah
                    if 'SATUAN KERJA' in daftar_kolom_besar:
                        target_col = df_filtered.columns[daftar_kolom_besar.index('SATUAN KERJA')]
                    elif 'KODE SATKER' in daftar_kolom_besar:
                        target_col = df_filtered.columns[daftar_kolom_besar.index('KODE SATKER')]
                    
                    if target_col:
                        df_filtered = df_filtered[df_filtered[target_col].astype(str).str.contains(search_satker, case=False, na=False)]
                    else:
                        st.warning("Kolom Satker tidak ditemukan.")

        # LOGIKA FILTER BULAN 
        if use_bulan:
            with in2:
                list_bulan_custom = ["JANUARI", "FEBRUARI", "MARET", "APRIL", "MEI", "JUNI", 
                                     "JULI", "AGUSTUS", "SEPTEMBER", "OKTOBER", "NOVEMBER", "DESEMBER",
                                     "THR", "GAJI 13"]
                pilih_bulan = st.selectbox("Pilih Periode:", ["Semua"] + list_bulan_custom, key="sb_bulan_gaji")
                
                if pilih_bulan != "Semua":
                    cols_upper = [c.upper() for c in df_filtered.columns]
                    col_bulan = None
                    
                    if 'BULAN PERIODE ADK' in cols_upper:
                        col_bulan = df_filtered.columns[cols_upper.index('BULAN PERIODE ADK')]
                    elif 'BULAN PERIODE' in cols_upper:
                        col_bulan = df_filtered.columns[cols_upper.index('BULAN PERIODE')]
                    
                    if col_bulan:
                        kata_kunci = pilih_bulan if pilih_bulan in ["THR", "GAJI 13"] else pilih_bulan[:3]
                        df_filtered = df_filtered[df_filtered[col_bulan].astype(str).str.upper().str.contains(kata_kunci, na=False)]

        # LOGIKA FILTER PEGAWAI
        if use_pegawai:
            with in3:
                cols_upper = [c.upper() for c in df_filtered.columns]
                if 'JENIS PEGAWAI' in cols_upper:
                    col_target = df_filtered.columns[cols_upper.index('JENIS PEGAWAI')]
                    list_pegawai = df_filtered[col_target].dropna().unique().tolist()
                    pilih_pegawai = st.selectbox("Pilih Jenis Pegawai:", ["Semua"] + list_pegawai, key="sb_pegawai_gaji")
                    if pilih_pegawai != "Semua":
                        df_filtered = df_filtered[df_filtered[col_target] == pilih_pegawai]

        # LOGIKA FILTER STATUS
        if use_status:
            with in4:
                cols_upper = [c.upper() for c in df_filtered.columns]
                if 'STATUS ADK' in cols_upper:
                    col_target = df_filtered.columns[cols_upper.index('STATUS ADK')]
                    list_status = df_filtered[col_target].dropna().unique().tolist()
                    pilih_status = st.selectbox("Pilih Status:", ["Semua"] + list_status, key="sb_status_gaji")
                    if pilih_status != "Semua":
                        df_filtered = df_filtered[df_filtered[col_target] == pilih_status]

        st.markdown("---")
        
       # 4. MENAMPILKAN TABEL DETAIL
        st.markdown('<h3 style="color:#283593; font-size:18px;">Detail Data Rekon Gaji</h3>', unsafe_allow_html=True)
        st.markdown('<p style="font-size: 13.5px; color: #666666; font-style: italic; margin-top: -10px; margin-bottom: 15px;">* Petunjuk: Arahkan kursor atau klik 2 kali pada sel tabel untuk melihat isi teks keterangan yang panjang secara lengkap.</p>', unsafe_allow_html=True)
        
        # Target nama kolom rapi yang diinginkan
        kolom_target = ['Timestamp', 'Satuan Kerja', 'Jenis Pegawai', 'Apa jenis proses yang sedang diajukan?', 'REKON ADK', 'PENGHAPUSAN/PEMBATALAN ADK', 'Bulan Periode ADK', 'Status ADK', 'Keterangan']
        
        kolom_tersedia = []
        kamus_perbaikan_nama = {}
        
        # Mesin pencari 
        for target in kolom_target:
            target_bersih = str(target).upper().replace(" ", "")
            
            for col_excel in df_filtered.columns:
                col_excel_bersih = str(col_excel).upper().replace(" ", "")
                
                if target_bersih == col_excel_bersih:
                    kolom_tersedia.append(col_excel)
                    kamus_perbaikan_nama[col_excel] = target
                    break
        
        # Potong tabel hanya dengan kolom yang berhasil ditemukan
        df_tampil = df_filtered[kolom_tersedia].reset_index(drop=True)
        
        # Rapikan otomatis judul kolom di aplikasi agar sesuai dengan 'kolom_target'
        df_tampil = df_tampil.rename(columns=kamus_perbaikan_nama)
        # FUNGSI PEWARNAAN BARIS 
        def warnai_baris(row):
            if 'Status ADK' in row and row['Status ADK'] in ['Dikembalikan', 'Ditolak']:
                return ['background-color: #d32f2f; color: #ffffff; font-weight: 500;'] * len(row)
            return [''] * len(row)
            
        df_berwarna = df_tampil.style.apply(warnai_baris, axis=1)
        
        # MENAMPILKAN TABEL
        st.dataframe(
            df_berwarna, 
            use_container_width=True,
            hide_index=True, 
            column_config={
                "Timestamp": st.column_config.DatetimeColumn("Timestamp", format="DD MMM YYYY HH:mm", width="medium"),
                "Keterangan": st.column_config.TextColumn("Keterangan", width="medium"),
                "Satuan Kerja": st.column_config.TextColumn("Satuan Kerja", width="medium")
            }
        )
        
        st.caption(f"Menampilkan {len(df_tampil)} baris data berdasarkan filter yang dipilih.")
    else:
        st.info("Menunggu data Rekon Gaji ditarik dari sistem...")

# HALAMAN REKON GAJI
elif menu == "PPNPN":
    st.markdown('<h1 style="color:#283593;">REKON GAJI PPNPN</h1>', unsafe_allow_html=True)
    st.markdown(f'<p class="interval-text">Interval update data setiap {INTERVAL_MENIT} menit</p>', unsafe_allow_html=True)
    
    # HILANGKAN FITUR DOWNLOAD EXCEL/CSV (Toolbar)
    st.markdown("""
        <style>
        [data-testid="stElementToolbar"] {
            display: none !important;
        }
        </style>
    """, unsafe_allow_html=True)

    if not df_ppnpn.empty:
        # 1. UBAH TYPE TIMESTAMP JADI DATE & SORT DATA TERBARU
        if 'Timestamp' in df_ppnpn.columns:
            df_ppnpn['Timestamp'] = pd.to_datetime(df_ppnpn['Timestamp'], errors='coerce', dayfirst=True)
            df_ppnpn = df_ppnpn.sort_values(by='Timestamp', ascending=False)

        # 2. PERSIAPAN DATA SATKER 
        # if 'Kode Satker' in df_ppnpn.columns:
        #     satker_split = df_ppnpn['Kode Satker'].astype(str).str.split('-', n=1, expand=True)
        #     if satker_split.shape[1] == 2:
        #         df_ppnpn['Kode Satker'] = satker_split[0].str.strip()
        #         df_ppnpn['Nama Satker'] = satker_split[1].str.strip()
        #     else:
        #         df_ppnpn['Kode Satker'] = df_ppnpn['Satuan Kerja']
        #         df_ppnpn['Nama Satker'] = df_ppnpn['Satuan Kerja']
                
        #     # Tabel Daftar Satker (Bagian Atas)
        #     st.markdown('<h3 style="color:#283593; font-size:18px;">Daftar Satker</h3>', unsafe_allow_html=True)
        #     df_satker_list = df_ppnpn[['Kode Satker', 'Nama Satker']].drop_duplicates().reset_index(drop=True)
        #     df_satker_list.index += 1 
        #     st.dataframe(df_satker_list, use_container_width=True, height=200) 
        # st.write("")

        # 3. SISTEM FILTER DINAMIS
        st.markdown('<h3 style="color:#283593; font-size:18px;">Filter Data Detail</h3>', unsafe_allow_html=True)
        cb1, cb2, cb3, cb4 = st.columns(4)
        
        use_satker = cb1.checkbox("Filter Satker (Kode/Nama)", key="cb_satker_ppnpn")
        use_bulan = cb2.checkbox("Filter Bulan", key="cb_bulan_ppnpn")
        use_jenis = cb3.checkbox("Filter Jenis ADK", key="cb_jenis_ppnpn")
        use_status = cb4.checkbox("Filter Status ADK", key="cb_status_ppnpn")

        df_filtered = df_ppnpn.copy()
        in1, in2, in3, in4 = st.columns(4)
        
        # LOGIKA FILTER SATKER
        if use_satker:
            with in1:
                search_satker = st.text_input("Ketik Kode/Nama Satker:", key="in_satker_ppnpn")
                if search_satker:
                    daftar_kolom_besar = [c.upper() for c in df_filtered.columns]
                    target_col = None
                    
                    # Cek prioritas kolom yang akan digeledah
                    if 'SATUAN KERJA' in daftar_kolom_besar:
                        target_col = df_filtered.columns[daftar_kolom_besar.index('SATUAN KERJA')]
                    elif 'KODE SATKER' in daftar_kolom_besar:
                        target_col = df_filtered.columns[daftar_kolom_besar.index('KODE SATKER')]
                    
                    if target_col:
                        df_filtered = df_filtered[df_filtered[target_col].astype(str).str.contains(search_satker, case=False, na=False)]
                    else:
                        st.warning("Kolom Satker tidak ditemukan.")

        # LOGIKA FILTER BULAN
        if use_bulan:
            with in2:
                list_bulan_custom = ["JANUARI", "FEBRUARI", "MARET", "APRIL", "MEI", "JUNI", 
                                     "JULI", "AGUSTUS", "SEPTEMBER", "OKTOBER", "NOVEMBER", "DESEMBER",
                                     "THR", "GAJI 13"]
                pilih_bulan = st.selectbox("Pilih Periode:", ["Semua"] + list_bulan_custom, key="sb_bulan_ppnpn")
                
                if pilih_bulan != "Semua":
                    cols_upper = [c.upper() for c in df_filtered.columns]
                    col_bulan = None
                    
                    if 'BULAN PERIODE ADK' in cols_upper:
                        col_bulan = df_filtered.columns[cols_upper.index('BULAN PERIODE ADK')]
                    elif 'BULAN PERIODE' in cols_upper:
                        col_bulan = df_filtered.columns[cols_upper.index('BULAN PERIODE')]
                    
                    if col_bulan:
                        kata_kunci = pilih_bulan if pilih_bulan in ["THR", "GAJI 13"] else pilih_bulan[:3]
                        df_filtered = df_filtered[df_filtered[col_bulan].astype(str).str.upper().str.contains(kata_kunci, na=False)]

        # LOGIKA FILTER JENIS ADK
        if use_jenis:
            with in3:
                cols_upper = [c.upper() for c in df_filtered.columns]
                if 'JENIS ADK' in cols_upper:
                    col_target = df_filtered.columns[cols_upper.index('JENIS ADK')]
                    list_jenis = df_filtered[col_target].dropna().unique().tolist()
                    pilih_jenis = st.selectbox("Pilih Jenis ADK:", ["Semua"] + list_jenis, key="sb_jenis_ppnpn")
                    if pilih_jenis != "Semua":
                        df_filtered = df_filtered[df_filtered[col_target] == pilih_jenis]

        # LOGIKA FILTER STATUS
        if use_status:
            with in4:
                cols_upper = [c.upper() for c in df_filtered.columns]
                if 'STATUS ADK' in cols_upper:
                    col_target = df_filtered.columns[cols_upper.index('STATUS ADK')]
                    list_status = df_filtered[col_target].dropna().unique().tolist()
                    pilih_status = st.selectbox("Pilih Status:", ["Semua"] + list_status, key="sb_status_ppnpn")
                    if pilih_status != "Semua":
                        df_filtered = df_filtered[df_filtered[col_target] == pilih_status]

        st.markdown("---")
        
        # 4. MENAMPILKAN TABEL DETAIL
        st.markdown('<h3 style="color:#283593; font-size:18px;">Detail Data Rekon PPNPN</h3>', unsafe_allow_html=True)
        st.markdown('<p style="font-size: 13.5px; color: #666666; font-style: italic; margin-top: -10px; margin-bottom: 15px;">* Petunjuk: Arahkan kursor atau klik 2 kali pada sel tabel untuk melihat isi teks keterangan yang panjang secara lengkap.</p>', unsafe_allow_html=True)
        
        # Target nama kolom
        kolom_target = ['Timestamp', 'Kode Satker', 'Kode Anak Satker', 'Jenis ADK', 'ID ADK yang Diajukan', 'Bulan Periode', 'Status ADK', 'Keterangan']
        
        kolom_tersedia = []
        kamus_perbaikan_nama = {}
        
        # Mesin pencari 
        for target in kolom_target:
            target_bersih = str(target).upper().replace(" ", "")
            
            for col_excel in df_filtered.columns:
                col_excel_bersih = str(col_excel).upper().replace(" ", "")
                
                if target_bersih == col_excel_bersih:
                    kolom_tersedia.append(col_excel)
                    kamus_perbaikan_nama[col_excel] = target
                    break
        
        # Potong tabel hanya dengan kolom yang berhasil ditemukan
        df_tampil = df_filtered[kolom_tersedia].reset_index(drop=True)
        
        # Merapikan otomatis judul kolom di aplikasi agar sesuai dengan 'kolom_target'
        df_tampil = df_tampil.rename(columns=kamus_perbaikan_nama)
        
        # FUNGSI PEWARNAAN BARIS 
        def warnai_baris(row):
            if 'Status ADK' in row and row['Status ADK'] in ['Dikembalikan', 'Ditolak']:
                return ['background-color: #d32f2f; color: #ffffff; font-weight: 500;'] * len(row)
            return [''] * len(row)
            
        df_berwarna = df_tampil.style.apply(warnai_baris, axis=1)
        
        # MENAMPILKAN TABEL 
        st.dataframe(
            df_berwarna, 
            use_container_width=True,
            hide_index=True, 
            column_config={
                "Timestamp": st.column_config.DatetimeColumn("Timestamp", format="DD MMM YYYY HH:mm", width="medium"),
                "Keterangan": st.column_config.TextColumn("Keterangan", width="medium"),
                "Satuan Kerja": st.column_config.TextColumn("Satuan Kerja", width="medium")
            }
        )
        
        st.caption(f"Menampilkan {len(df_tampil)} baris data berdasarkan filter yang dipilih.")

    else:
        st.info("Menunggu data Rekon Gaji PPNPN ditarik dari sistem...")

# HALAMAN SKPP
elif menu == "SKPP":
    st.markdown('<h1 style="color:#283593;">PENGAJUAN SKPP</h1>', unsafe_allow_html=True)
    st.markdown(f'<p class="interval-text">Interval update data setiap {INTERVAL_MENIT} menit</p>', unsafe_allow_html=True)
    
    # HILANGKAN FITUR DOWNLOAD EXCEL/CSV (Toolbar)
    st.markdown("""
        <style>
        [data-testid="stElementToolbar"] {
            display: none !important;
        }
        </style>
    """, unsafe_allow_html=True)

    if not df_skpp.empty:
        # 1. UBAH TYPE TIMESTAMP JADI DATE & SORT DATA TERBARU
        if 'Timestamp' in df_skpp.columns:
            df_skpp['Timestamp'] = pd.to_datetime(df_skpp['Timestamp'], errors='coerce', dayfirst=True)
            df_skpp = df_skpp.sort_values(by='Timestamp', ascending=False)

        # 2. PERSIAPAN DATA SATKER 
        # if 'Kode Satker' in df_skpp.columns:
        #     satker_split = df_skpp['Kode Satker'].astype(str).str.split('-', n=1, expand=True)
        #     if satker_split.shape[1] == 2:
        #         df_skpp['Kode Satker'] = satker_split[0].str.strip()
        #         df_skpp['Nama Satker'] = satker_split[1].str.strip()
        #     else:
        #         df_skpp['Kode Satker'] = df_skpp['Kode Satker']
        #         df_skpp['Nama Satker'] = df_skpp['Kode Satker']
                
        #     # Tabel Daftar Satker (Bagian Atas)
        #     st.markdown('<h3 style="color:#283593; font-size:18px;">Daftar Satker</h3>', unsafe_allow_html=True)
        #     df_satker_list = df_skpp[['Kode Satker', 'Nama Satker']].drop_duplicates().reset_index(drop=True)
        #     df_satker_list.index += 1 
        #     st.dataframe(df_satker_list, use_container_width=True, height=200) 
        # st.write("")

        # 3. SISTEM FILTER DINAMIS
        st.markdown('<h3 style="color:#283593; font-size:18px;">Filter Data Detail</h3>', unsafe_allow_html=True)
        cb1, cb2, cb3, cb4, cb5 = st.columns(5)
        
        use_satker = cb1.checkbox("Filter Satker (Kode/Nama)", key="cb_satker_skpp")
        use_bulan = cb2.checkbox("Filter Bulan", key="cb_bulan_skpp")
        use_pegawai = cb3.checkbox("Filter Jenis Pegawai", key="cb_pegawai_skpp")
        use_jenis_skpp = cb4.checkbox("Filter Jenis SKPP", key="cb_jenis_skpp") 
        use_status = cb5.checkbox("Filter Status FO", key="cb_status_skpp")   

        df_filtered = df_skpp.copy()
        in1, in2, in3, in4, in5 = st.columns(5)
        
        # LOGIKA FILTER SATKER 
        if use_satker:
            with in1:
                search_satker = st.text_input("Ketik Kode/Nama Satker:", key="in_satker_skpp")
                if search_satker:
                    daftar_kolom_besar = [c.upper() for c in df_filtered.columns]
                    target_col = None
                    
                    # Cek prioritas kolom yang akan digeledah
                    if 'SATUAN KERJA' in daftar_kolom_besar:
                        target_col = df_filtered.columns[daftar_kolom_besar.index('SATUAN KERJA')]
                    elif 'KODE SATKER' in daftar_kolom_besar:
                        target_col = df_filtered.columns[daftar_kolom_besar.index('KODE SATKER')]
                    
                    if target_col:
                        df_filtered = df_filtered[df_filtered[target_col].astype(str).str.contains(search_satker, case=False, na=False)]
                    else:
                        st.warning("Kolom Satker tidak ditemukan.")

        # LOGIKA FILTER BULAN 
        if use_bulan:
            with in2:
                list_bulan_custom = ["JANUARI", "FEBRUARI", "MARET", "APRIL", "MEI", "JUNI", 
                                     "JULI", "AGUSTUS", "SEPTEMBER", "OKTOBER", "NOVEMBER", "DESEMBER"]
                pilih_bulan = st.selectbox("Pilih Periode:", ["Semua"] + list_bulan_custom, key="sb_bulan_skpp")
                
                if pilih_bulan != "Semua":
                    cols_upper = [c.upper() for c in df_filtered.columns]
                    col_bulan = None
                    
                    if 'BULAN PERIODE ADK' in cols_upper:
                        col_bulan = df_filtered.columns[cols_upper.index('BULAN PERIODE ADK')]
                    elif 'BULAN PERIODE' in cols_upper:
                        col_bulan = df_filtered.columns[cols_upper.index('BULAN PERIODE')]
                    
                    if col_bulan:
                        kata_kunci = pilih_bulan[:3]
                        df_filtered = df_filtered[df_filtered[col_bulan].astype(str).str.upper().str.contains(kata_kunci, na=False)]

        # LOGIKA FILTER PEGAWAI
        if use_pegawai:
            with in3:
                cols_upper = [c.upper() for c in df_filtered.columns]
                if 'JENIS PEGAWAI' in cols_upper:
                    col_target = df_filtered.columns[cols_upper.index('JENIS PEGAWAI')]
                    list_pegawai = df_filtered[col_target].dropna().unique().tolist()
                    pilih_pegawai = st.selectbox("Pilih Jenis Pegawai:", ["Semua"] + list_pegawai, key="sb_pegawai_skpp")
                    if pilih_pegawai != "Semua":
                        df_filtered = df_filtered[df_filtered[col_target] == pilih_pegawai]

        # LOGIKA FILTER JENIS SKPP
        if use_jenis_skpp:
            with in4:
                cols_upper = [c.upper() for c in df_filtered.columns]
                if 'JENIS SKPP' in cols_upper:
                    col_target = df_filtered.columns[cols_upper.index('JENIS SKPP')]
                    list_jenis_skpp = df_filtered[col_target].dropna().unique().tolist()
                    pilih_jenis_skpp = st.selectbox("Pilih Jenis SKPP:", ["Semua"] + list_jenis_skpp, key="sb_jenis_skpp")
                    if pilih_jenis_skpp != "Semua":
                        df_filtered = df_filtered[df_filtered[col_target] == pilih_jenis_skpp]
        
        # LOGIKA FILTER STATUS
        if use_status:
            with in5:
                cols_upper = [c.upper() for c in df_filtered.columns]
                if 'STATUS FO' in cols_upper:
                    col_target = df_filtered.columns[cols_upper.index('STATUS FO')]
                    list_status = df_filtered[col_target].dropna().unique().tolist()
                    pilih_status = st.selectbox("Pilih Status:", ["Semua"] + list_status, key="sb_status_skpp")
                    if pilih_status != "Semua":
                        df_filtered = df_filtered[df_filtered[col_target] == pilih_status]

        st.markdown("---")
        
        # Tampilkan Tabel Detail
        st.markdown('<h3 style="color:#283593; font-size:18px;">Detail Data Pengajuan SKPP</h3>', unsafe_allow_html=True)
        st.markdown('<p style="font-size: 13.5px; color: #666666; font-style: italic; margin-top: -10px; margin-bottom: 15px;">* Petunjuk: Arahkan kursor atau klik 2 kali pada sel tabel untuk melihat isi teks keterangan yang panjang secara lengkap.</p>', unsafe_allow_html=True)
        
        kolom_target = ['Timestamp', 'Kode Satker', 'Jenis Pegawai', 'Jenis SKPP', 'Nomor SKPP', 'Nama Pegawai', 'Bulan Periode', 'Status FO', 'TTD Kasi PD', 'Keterangan']
        
        kolom_tersedia = []
        kamus_perbaikan_nama = {}
        
        # Mesin pencari kolom pintar
        for target in kolom_target:
            # Bersihkan targe
            target_bersih = str(target).upper().replace(" ", "")
            
            for col_excel in df_filtered.columns:
                col_excel_bersih = str(col_excel).upper().replace(" ", "")
                
                # Jika cocok, simpan nama aslinya untuk ditarik datanya nanti
                if target_bersih == col_excel_bersih:
                    kolom_tersedia.append(col_excel)
                    kamus_perbaikan_nama[col_excel] = target
                    break 
        
        # Potong tabel hanya dengan kolom yang berhasil ditemukan
        df_tampil = df_filtered[kolom_tersedia].reset_index(drop=True)
        
        # Rapikan judul kolom di tabel aplikasi agar bentuk tulisan dan spasinya sempurna (meskipun di Excel berantakan)
        df_tampil = df_tampil.rename(columns=kamus_perbaikan_nama)

        # FUNGSI PEWARNAAN BARIS 
        def warnai_baris(row):
            if 'Status ADK' in row and row['Status ADK'] in ['Dikembalikan', 'Ditolak']:
                return ['background-color: #d32f2f; color: #ffffff; font-weight: 500;'] * len(row)
            return [''] * len(row)
            
        df_berwarna = df_tampil.style.apply(warnai_baris, axis=1)
        
        # MENAMPILKAN TABEL
        st.dataframe(
            df_berwarna, 
            use_container_width=True,
            hide_index=True, 
            column_config={
                "Timestamp": st.column_config.DatetimeColumn("Timestamp", format="DD MMM YYYY HH:mm", width="medium"),
                "Keterangan": st.column_config.TextColumn("Keterangan", width="medium"),
                "Satuan Kerja": st.column_config.TextColumn("Satuan Kerja", width="medium")
            }
        )
        
        st.caption(f"Menampilkan {len(df_tampil)} baris data berdasarkan filter yang dipilih.")

    else:
        st.info("Menunggu data Rekon Gaji ditarik dari sistem...")
