import streamlit as st
import pandas as pd
import plotly.express as px

# KONFIGURASI HALAMAN
st.set_page_config(layout="wide", page_title="Monitoring Bokori 2026", page_icon=" ")

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
    st.markdown("<h3 style='text-align: center; color: #283593;'>DASHBOARD BOKORI</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 12px; color: gray; margin-top:-15px;'>KPPN Kendari</p>", unsafe_allow_html=True)
    
    # Gunakan variabel menu_utama
    menu = st.radio("menu_utama", ["OVERVIEW", "REKON GAJI", "PPNPN", "SKPP"], index=0)
    
    st.write("---")
    # Referensi Status Live
    st.markdown('<div style="text-align:center; padding: 10px; background-color: #e8f5e9; border-radius: 25px; color: #2e7d32; font-size: 11px; font-weight: bold;">STATUS: TERHUBUNG (LIVE)</div>', unsafe_allow_html=True)

# HALAMAN OVERVIEW
if menu == "OVERVIEW":
    st.markdown("<div style='padding-top: 50px;'></div>", unsafe_allow_html=True)
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
            st.metric("Volume ASN", f"{len(df_rekon):,}".replace(',', '.'))

    with m3:
        with st.container():
            st.metric("Volume PPNPN", f"{len(df_ppnpn):,}".replace(',', '.'))

    with m4:
        with st.container():
            st.metric("Volume SKPP", f"{len(df_skpp):,}".replace(',', '.'))

    st.markdown("<div style='margin-bottom: 30px;'></div>", unsafe_allow_html=True)

    st.write("")

    # ANALISIS TREN & STATUS
    c1, c2 = st.columns([1.6, 1])

    with c1:
        st.markdown('<h3 style="color:#283593; font-size:18px; margin-bottom:10px;">Perbandingan Aktivitas Bulanan</h3>', unsafe_allow_html=True)
        try:
            # Fungsi pelacak kolom bulan otomatis
            def ambil_bulan(df, nama_sumber):
                for col in df.columns:
                    if 'bulan' in col.lower():
                        temp = df[[col]].dropna().copy()
                        temp.columns = ['Bulan Mentah']
                        temp['Sumber'] = nama_sumber
                        return temp
                return pd.DataFrame(columns=['Bulan Mentah', 'Sumber'])

            b1 = ambil_bulan(df_rekon, 'ASN')
            b2 = ambil_bulan(df_ppnpn, 'PPNPN')
            b3 = ambil_bulan(df_skpp, 'SKPP')

            df_all_bulan = pd.concat([b1, b2, b3])

            if not df_all_bulan.empty:
                import re
                mapping_bulan = {
                    'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
                    'mei': '05', 'jun': '06', 'jul': '07', 'agu': '08',
                    'sep': '09', 'okt': '10', 'nov': '11', 'des': '12'
                }

                # Standarisasi format waktu
                def standarisasi_tanggal(teks):
                    teks_lower = str(teks).lower()
                    tahun_match = re.search(r'\d{4}', teks_lower)
                    tahun = tahun_match.group() if tahun_match else "2026"
                    
                    bulan_angka = "01"
                    for indo, angka in mapping_bulan.items():
                        if indo in teks_lower:
                            bulan_angka = angka
                            break
                    return f"{tahun}-{bulan_angka}-01"

                df_all_bulan['Tanggal Baku'] = df_all_bulan['Bulan Mentah'].apply(standarisasi_tanggal)
                df_all_bulan['Tanggal Baku'] = pd.to_datetime(df_all_bulan['Tanggal Baku'], errors='coerce')
                
                df_trend_mentah = df_all_bulan.groupby(['Tanggal Baku', 'Sumber']).size().reset_index(name='Jumlah')
                
                # Filter tahun & tambal bulan kosong
                df_trend_mentah = df_trend_mentah[df_trend_mentah['Tanggal Baku'].dt.year >= 2025]
                df_pivot = df_trend_mentah.pivot(index='Tanggal Baku', columns='Sumber', values='Jumlah').fillna(0).reset_index()
                sumber_tersedia = [col for col in ['ASN', 'PPNPN', 'SKPP'] if col in df_pivot.columns]
                df_trend = df_pivot.melt(id_vars='Tanggal Baku', value_vars=sumber_tersedia, var_name='Sumber', value_name='Jumlah')
                
                df_trend = df_trend.sort_values(by='Tanggal Baku')
                df_trend.rename(columns={'Tanggal Baku': 'Bulan', 'Sumber': 'Loket Layanan'}, inplace=True)

                # Menggambar grafik
                fig_line = px.line(df_trend, x='Bulan', y='Jumlah', color='Loket Layanan', 
                                   markers=True, line_shape="spline", 
                                   color_discrete_map={"ASN": "#283593", "PPNPN": "#c62828", "SKPP": "#00897b"})
                
                fig_line.update_traces(line=dict(width=3), marker=dict(size=8))
                
                fig_line.update_layout(
                    xaxis=dict(
                        title="Periode Bulan",
                        tickformat="%b %Y",     # Format: Jan 2026, Feb 2026
                        tickmode="linear",      # MEMAKSA mesin berhitung urut (tidak auto-hide)
                        dtick="M1",             # Jarak antar label wajib 1 bulan
                        tickangle=-45,          # Teks dimiringkan 45 derajat agar rapi
                        showticklabels=True,    # Fitur wajib untuk memunculkan teksnya
                        showgrid=True,
                        gridcolor='rgba(200, 200, 200, 0.2)'
                    ),
                    yaxis=dict(
                        title="Volume Pengajuan",
                        showgrid=True,
                        gridcolor='rgba(200, 200, 200, 0.2)'
                    ),
                    hovermode="x unified", 
                    plot_bgcolor='rgba(0,0,0,0)', 
                    paper_bgcolor='rgba(0,0,0,0)', 
                    legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5), 
                    margin=dict(l=0, r=0, t=40, b=0), 
                    height=420 
                )
                
                st.plotly_chart(fig_line, use_container_width=True, theme=None)
            else:
                st.info("Belum ada data bulan yang tercatat.")
        except Exception as e:
            st.error(f"Gagal memuat grafik tren: {str(e)}")

    with c2:
        st.markdown('<h3 style="color:#283593; font-size:18px; margin-bottom:10px;">Persentase Status Global</h3>', unsafe_allow_html=True)
        try:
            # Ambil data status dari 3 sheet
            s1 = df_rekon['Status ADK'].dropna().astype(str) if 'Status ADK' in df_rekon.columns else pd.Series(dtype='str')
            s2 = df_ppnpn['Status ADK'].dropna().astype(str) if 'Status ADK' in df_ppnpn.columns else pd.Series(dtype='str')
            s3 = df_skpp['Status'].dropna().astype(str) if 'Status' in df_skpp.columns else pd.Series(dtype='str')

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

                # Buat Grafik Donut (Legenda bawaan dimatikan agar bersih)
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

                # LEGENDA MASTER DINAMIS (Muncul otomatis berdasarkan data)
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
        kategori_ditemukan = {} # Untuk simpan mapping Kategori -> Warna
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
    titles = ["Layanan ASN", "Layanan PPNPN", "Layanan SKPP"]
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
elif menu == "REKON GAJI":
    st.markdown('<h1 style="color:#283593;">GAJI ASN (REKON GAJI)</h1>', unsafe_allow_html=True)
    st.markdown(f'<p class="interval-text">Interval update data setiap {INTERVAL_MENIT} menit</p>', unsafe_allow_html=True)
    
    if not df_rekon.empty:
        # PERSIAPAN DATA SATKER (Memecah Kode dan Nama)
        if 'Satuan Kerja' in df_rekon.columns:
            satker_split = df_rekon['Satuan Kerja'].astype(str).str.split('-', n=1, expand=True)
            if satker_split.shape[1] == 2:
                df_rekon['Kode Satker'] = satker_split[0].str.strip()
                df_rekon['Nama Satker'] = satker_split[1].str.strip()
            else:
                df_rekon['Kode Satker'] = df_rekon['Satuan Kerja']
                df_rekon['Nama Satker'] = df_rekon['Satuan Kerja']
                
            # Tabel Daftar Satker (Bagian Atas)
            st.markdown('<h3 style="color:#283593; font-size:18px;">Daftar Satker</h3>', unsafe_allow_html=True)
            df_satker_list = df_rekon[['Kode Satker', 'Nama Satker']].drop_duplicates().reset_index(drop=True)
            df_satker_list.index += 1 
            st.dataframe(df_satker_list, use_container_width=True, height=200) 
        
        st.write("")
        

        st.markdown('<h3 style="color:#283593; font-size:18px;">Filter Data Detail</h3>', unsafe_allow_html=True)
        cb1, cb2, cb3, cb4 = st.columns(4)
        use_satker = cb1.checkbox("Filter Satker (Kode/Nama)")
        use_bulan = cb2.checkbox("Filter Bulan")
        use_pegawai = cb3.checkbox("Filter Jenis Pegawai")
        use_status = cb4.checkbox("Filter Status ADK")
        
        df_filtered = df_rekon.copy()
        in1, in2, in3, in4 = st.columns(4)
        
        if use_satker:
            with in1:
                search_satker = st.text_input("Ketik Kode/Nama Satker:")
                if search_satker:
                    df_filtered = df_filtered[df_filtered['Satuan Kerja'].astype(str).str.contains(search_satker, case=False, na=False)]
                    
        if use_bulan:
            with in2:
                col_bulan = 'Bulan Periode ADK' if 'Bulan Periode ADK' in df_rekon.columns else 'Bulan Periode / Petugas'
                if col_bulan in df_rekon.columns:
                    list_bulan = df_rekon[col_bulan].dropna().unique().tolist()
                    pilih_bulan = st.selectbox("Pilih Bulan:", ["Semua"] + list_bulan)
                    if pilih_bulan != "Semua":
                        df_filtered = df_filtered[df_filtered[col_bulan] == pilih_bulan]
                        
        if use_pegawai:
            with in3:
                if 'Jenis Pegawai' in df_rekon.columns:
                    list_pegawai = df_rekon['Jenis Pegawai'].dropna().unique().tolist()
                    pilih_pegawai = st.selectbox("Pilih Jenis Pegawai:", ["Semua"] + list_pegawai)
                    if pilih_pegawai != "Semua":
                        df_filtered = df_filtered[df_filtered['Jenis Pegawai'] == pilih_pegawai]
                        
        if use_status:
            with in4:
                if 'Status ADK' in df_rekon.columns:
                    list_status = df_rekon['Status ADK'].dropna().unique().tolist()
                    pilih_status = st.selectbox("Pilih Status:", ["Semua"] + list_status)
                    if pilih_status != "Semua":
                        df_filtered = df_filtered[df_filtered['Status ADK'] == pilih_status]

        st.markdown("---")
        
        # MENAMPILKAN TABEL DETAIL HASIL FILTER
        st.markdown('<h3 style="color:#283593; font-size:18px;">Detail Data Rekon Gaji</h3>', unsafe_allow_html=True)
        st.markdown('<p style="font-size: 13.5px; color: #666666; font-style: italic; margin-top: -10px; margin-bottom: 15px;">* Petunjuk: Arahkan kursor atau klik 2 kali pada sel tabel untuk melihat isi teks keterangan yang panjang secara lengkap.</p>', unsafe_allow_html=True)
        
        kolom_target = ['Timestamp', 'Satuan Kerja', 'Bulan Periode ADK', 'Jenis Pegawai', 'REKON ADK', 'Status ADK', 'Keterangan']
        kolom_tersedia = [kol for kol in kolom_target if kol in df_filtered.columns]   
        
        df_tampil = df_filtered[kolom_tersedia].reset_index(drop=True)
        df_tampil.index += 1
        
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
            column_config={
                "Keterangan": st.column_config.TextColumn(
                    "Keterangan",
                    width="medium" 
                ),
                "Satuan Kerja": st.column_config.TextColumn(
                    "Satuan Kerja",
                    width="medium"
                )
            }
        )
        
        st.caption(f"Menampilkan {len(df_tampil)} baris data berdasarkan filter yang dipilih.")

    else:
        st.info("Menunggu data Rekon Gaji ditarik dari sistem...")


#  HALAMAN PPNPN
elif menu == "PPNPN":
    st.markdown('<h1 style="color:#283593;">GAJI PPNPN</h1>', unsafe_allow_html=True)
    st.markdown(f'<p class="interval-text">Interval update data setiap {INTERVAL_MENIT} menit</p>', unsafe_allow_html=True)
    
    if not df_ppnpn.empty:
        # PERSIAPAN DATA SATKER (Memecah Kode dan Nama dari kolom 'Kode Satker')
        if 'Kode Satker' in df_ppnpn.columns:
            # Memisahkan string berdasarkan tanda strip (-) pada kolom 'Kode Satker'
            satker_split = df_ppnpn['Kode Satker'].astype(str).str.split('-', n=1, expand=True)
            if satker_split.shape[1] == 2:
                df_ppnpn['Kode Satker'] = satker_split[0].str.strip() # Mengganti isi dengan kode saja
                df_ppnpn['Nama Satker'] = satker_split[1].str.strip() # Membuat kolom baru untuk Nama
            else:
                df_ppnpn['Nama Satker'] = df_ppnpn['Kode Satker']
                
            # Tabel Daftar Satker (Bagian Atas)
            st.markdown('<h3 style="color:#283593; font-size:18px;">Daftar Satker</h3>', unsafe_allow_html=True)
            df_satker_list = df_ppnpn[['Kode Satker', 'Nama Satker']].drop_duplicates().reset_index(drop=True)
            df_satker_list.index += 1 
            st.dataframe(df_satker_list, use_container_width=True, height=200) 
        
        st.write("")
        
        # SISTEM FILTER DINAMIS
        st.markdown('<h3 style="color:#283593; font-size:18px;">Filter Data Detail</h3>', unsafe_allow_html=True)
        
        cb1, cb2, cb3, cb4 = st.columns(4)
        use_satker = cb1.checkbox("Filter Satker (Kode/Nama)")
        use_bulan = cb2.checkbox("Filter Bulan")
        use_jenis = cb3.checkbox("Filter Jenis ADK")
        use_status = cb4.checkbox("Filter Status ADK")
        
        df_filtered = df_ppnpn.copy()
        in1, in2, in3, in4 = st.columns(4)
        
        if use_satker:
            with in1:
                search_satker = st.text_input("Ketik Kode/Nama Satker:")
                if search_satker:
                    # Mencari di Kode Satker, Nama Satker, atau Kode Anak Satker
                    kondisi = (
                        df_filtered['Kode Satker'].astype(str).str.contains(search_satker, case=False, na=False) |
                        df_filtered['Nama Satker'].astype(str).str.contains(search_satker, case=False, na=False)
                    )
                    if 'Kode Anak Satker' in df_filtered.columns:
                        kondisi = kondisi | df_filtered['Kode Anak Satker'].astype(str).str.contains(search_satker, case=False, na=False)
                    
                    df_filtered = df_filtered[kondisi]
                    
        if use_bulan:
            with in2:
                col_bulan = 'Bulan Periode' if 'Bulan Periode' in df_ppnpn.columns else 'Bulan Periode ADK'
                if col_bulan in df_ppnpn.columns:
                    list_bulan = df_ppnpn[col_bulan].dropna().unique().tolist()
                    pilih_bulan = st.selectbox("Pilih Bulan:", ["Semua"] + list_bulan)
                    if pilih_bulan != "Semua":
                        df_filtered = df_filtered[df_filtered[col_bulan] == pilih_bulan]
                        
        if use_jenis:
            with in3:
                if 'Jenis ADK' in df_ppnpn.columns:
                    list_jenis = df_ppnpn['Jenis ADK'].dropna().unique().tolist()
                    pilih_jenis = st.selectbox("Pilih Jenis ADK:", ["Semua"] + list_jenis)
                    if pilih_jenis != "Semua":
                        df_filtered = df_filtered[df_filtered['Jenis ADK'] == pilih_jenis]
                        
        if use_status:
            with in4:
                if 'Status ADK' in df_ppnpn.columns:
                    list_status = df_ppnpn['Status ADK'].dropna().unique().tolist()
                    pilih_status = st.selectbox("Pilih Status:", ["Semua"] + list_status)
                    if pilih_status != "Semua":
                        df_filtered = df_filtered[df_filtered['Status ADK'] == pilih_status]

        st.markdown("---")
        
        # MENAMPILKAN TABEL DETAIL HASIL FILTER
        st.markdown('<h3 style="color:#283593; font-size:18px;">Detail Data PPNPN</h3>', unsafe_allow_html=True)
        
        st.markdown('<p style="font-size: 13.5px; color: #666666; font-style: italic; margin-top: -10px; margin-bottom: 15px;">* Petunjuk: Arahkan kursor atau klik 2 kali pada sel tabel untuk melihat isi teks keterangan yang panjang secara lengkap.</p>', unsafe_allow_html=True)
        
        # Kolom target yang akan ditampilkan
        kolom_target = ['Timestamp', 'Bulan Periode', 'Kode Satker', 'Nama Satker', 'Kode Anak Satker', 'Jenis ADK', 'Status ADK', 'Keterangan']
        kolom_tersedia = [kol for kol in kolom_target if kol in df_filtered.columns]   
        
        df_tampil = df_filtered[kolom_tersedia].reset_index(drop=True)
        df_tampil.index += 1
        
        def warnai_baris(row):
            if 'Status ADK' in row and row['Status ADK'] in ['Dikembalikan', 'Ditolak']:
                return ['background-color: #d32f2f; color: #ffffff; font-weight: 500;'] * len(row)
            return [''] * len(row)
            
        df_berwarna = df_tampil.style.apply(warnai_baris, axis=1)
        
        st.dataframe(
            df_berwarna, 
            use_container_width=True,
            column_config={
                "Keterangan": st.column_config.TextColumn("Keterangan", help="Hover ke baris tabel untuk membaca seluruh teks.", width="medium"),
                "Nama Satker": st.column_config.TextColumn("Nama Satker", width="medium")
            }
        )
        
        st.caption(f"Menampilkan {len(df_tampil)} baris data berdasarkan filter yang dipilih.")

    else:
        st.info("Menunggu data PPNPN ditarik dari sistem...")

# HALAMAN SKPP
elif menu == "SKPP":
    st.markdown('<h1 style="color:#283593;">PENGAJUAN SKPP</h1>', unsafe_allow_html=True)
    st.markdown(f'<p class="interval-text">Interval update data setiap {INTERVAL_MENIT} menit</p>', unsafe_allow_html=True)
    
    if not df_skpp.empty:
        perbaikan_kolom = {
            'Timestamp1': 'Timestamp',
            'Jenis Pegawai2': 'Jenis Pegawai',
            'Nomor SKPP3': 'Nomor SKPP'
        }
        df_skpp.rename(columns=perbaikan_kolom, inplace=True)

        # PERSIAPAN DATA SATKER (Memecah Kode dan Nama)
        if 'Kode Satker' in df_skpp.columns:
            satker_split = df_skpp['Kode Satker'].astype(str).str.split('-', n=1, expand=True)
            if satker_split.shape[1] == 2:
                df_skpp['Kode Satker Bersih'] = satker_split[0].str.strip()
                df_skpp['Nama Satker'] = satker_split[1].str.strip()
            else:
                df_skpp['Kode Satker Bersih'] = df_skpp['Kode Satker']
                df_skpp['Nama Satker'] = df_skpp['Kode Satker']
                
            # Tabel Daftar Satker (Bagian Atas)
            st.markdown('<h3 style="color:#283593; font-size:18px;">Daftar Satker</h3>', unsafe_allow_html=True)
            df_satker_list = df_skpp[['Kode Satker Bersih', 'Nama Satker']].drop_duplicates().reset_index(drop=True)
            df_satker_list.rename(columns={'Kode Satker Bersih': 'Kode Satker'}, inplace=True) # Merapikan judul tabel
            df_satker_list.index += 1 
            st.dataframe(df_satker_list, use_container_width=True, height=200) 
        
        st.write("")
        
        # SISTEM FILTER DINAMIS
        st.markdown('<h3 style="color:#283593; font-size:18px;">Filter Data Detail</h3>', unsafe_allow_html=True)
        
        cb1, cb2, cb3, cb4 = st.columns(4)
        use_satker = cb1.checkbox("Filter Satker (Kode/Nama)")
        use_bulan = cb2.checkbox("Filter Bulan")
        use_jenis = cb3.checkbox("Filter Jenis SKPP")
        use_status = cb4.checkbox("Filter Status")
        
        df_filtered = df_skpp.copy()
        in1, in2, in3, in4 = st.columns(4)
        
        if use_satker:
            with in1:
                search_satker = st.text_input("Ketik Kode/Nama Satker:")
                if search_satker:
                    kondisi = (
                        df_filtered['Kode Satker Bersih'].astype(str).str.contains(search_satker, case=False, na=False) |
                        df_filtered['Nama Satker'].astype(str).str.contains(search_satker, case=False, na=False) |
                        df_filtered['Kode Satker'].astype(str).str.contains(search_satker, case=False, na=False)
                    )
                    df_filtered = df_filtered[kondisi]
                    
        if use_bulan:
            with in2:
                if 'Bulan Periode' in df_skpp.columns:
                    list_bulan = df_skpp['Bulan Periode'].dropna().unique().tolist()
                    pilih_bulan = st.selectbox("Pilih Bulan:", ["Semua"] + list_bulan)
                    if pilih_bulan != "Semua":
                        df_filtered = df_filtered[df_filtered['Bulan Periode'] == pilih_bulan]
                        
        if use_jenis:
            with in3:
                if 'Jenis SKPP' in df_skpp.columns:
                    list_jenis = df_skpp['Jenis SKPP'].dropna().unique().tolist()
                    pilih_jenis = st.selectbox("Pilih Jenis SKPP:", ["Semua"] + list_jenis)
                    if pilih_jenis != "Semua":
                        df_filtered = df_filtered[df_filtered['Jenis SKPP'] == pilih_jenis]
                        
        if use_status:
            with in4:
                col_status = 'Status' if 'Status' in df_skpp.columns else 'Status ADK'
                if col_status in df_skpp.columns:
                    list_status = df_skpp[col_status].dropna().unique().tolist()
                    pilih_status = st.selectbox("Pilih Status:", ["Semua"] + list_status)
                    if pilih_status != "Semua":
                        df_filtered = df_filtered[df_filtered[col_status] == pilih_status]

        st.markdown("---")
        
        # MENAMPILKAN TABEL DETAIL HASIL FILTER
        st.markdown('<h3 style="color:#283593; font-size:18px;">Detail Data SKPP</h3>', unsafe_allow_html=True)
        st.markdown('<p style="font-size: 13.5px; color: #666666; font-style: italic; margin-top: -10px; margin-bottom: 15px;">* Petunjuk: Arahkan kursor atau klik 2 kali pada sel tabel untuk melihat isi teks keterangan yang panjang secara lengkap.</p>', unsafe_allow_html=True)
        
        # Mengganti sementara kolom Kode Satker mentah menjadi yang bersih untuk ditampilkan
        if 'Kode Satker Bersih' in df_filtered.columns:
             df_filtered['Kode Satker'] = df_filtered['Kode Satker Bersih']

        # Mengatur urutan kolom yang akan ditampilkan
        kolom_target = ['Timestamp', 'Bulan Periode', 'Kode Satker', 'Nama Satker', 'Jenis Pegawai', 'Jenis SKPP', 'Nomor SKPP', 'Nama Pegawai', 'Keterangan', 'Status']
        kolom_tersedia = [kol for kol in kolom_target if kol in df_filtered.columns]   
        
        df_tampil = df_filtered[kolom_tersedia].reset_index(drop=True)
        df_tampil.index += 1
        
        # Fungsi pewarnaan baris merah solid untuk SKPP yang ditolak
        def warnai_baris(row):
            col_stat = 'Status' if 'Status' in row else ('Status ADK' if 'Status ADK' in row else None)
            if col_stat and row[col_stat] in ['Dikembalikan', 'Ditolak']:
                return ['background-color: #d32f2f; color: #ffffff; font-weight: 500;'] * len(row)
            return [''] * len(row)
            
        df_berwarna = df_tampil.style.apply(warnai_baris, axis=1)
        
        # Menampilkan tabel interaktif
        st.dataframe(
            df_berwarna, 
            use_container_width=True,
            column_config={
                "Keterangan": st.column_config.TextColumn(
                    "Keterangan", 
                    help="Hover (arahkan kursor) ke baris tabel untuk membaca seluruh teks keterangan.", 
                    width="medium"
                ),
                "Nama Satker": st.column_config.TextColumn(
                    "Nama Satker", 
                    width="medium"
                ),
                "Nama Pegawai": st.column_config.TextColumn(
                    "Nama Pegawai", 
                    width="medium"
                )
            }
        )
        
        st.caption(f"Menampilkan {len(df_tampil)} baris data berdasarkan filter yang dipilih.")

    else:
        st.info("Menunggu data SKPP ditarik dari sistem...")