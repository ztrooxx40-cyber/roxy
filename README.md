# Game Ular 2 Pemain

## Main di HP atau komputer yang sama

1. Buka `ular_2_pemain.html` di browser.
2. Pilih **Main 2 pemain**. Mode ini langsung berjalan tanpa server dan tanpa internet.
3. Di HP, gunakan dua panel arah pada layar. Di komputer, gunakan W/A/S/D dan tombol panah.

Tampilan dan kontrol sudah menyesuaikan layar HP, termasuk saat dipakai dalam orientasi mendatar.

## Main online dari mana saja

Mode online memerlukan server publik yang mendukung WebSocket. Agar dapat diakses teman lewat internet, deploy aplikasi ini ke Render:

1. Buat repository GitHub baru dan unggah **isi folder `game` ini** ke akar repository. Pastikan `render.yaml`, `server.py`, `requirements.txt`, dan `ular_2_pemain.html` berada di akar repository.
2. Di Render, pilih **New + → Blueprint**, lalu hubungkan repository tersebut. Render membaca `render.yaml` dan menjalankan server game.
3. Setelah deploy selesai, buka URL `https://...onrender.com` yang diberikan Render.
4. Pilih **Main online**, buat ruang, lalu bagikan kode atau tautan ruang kepada teman. Teman membuka URL publik yang sama.

Jangan gunakan alamat `localhost` atau `127.0.0.1` untuk teman; alamat itu hanya menunjuk ke perangkat sendiri. Jangan tutup server jika menggunakan hosting lokal.

Untuk tes lokal di komputer, klik dua kali `mulai_game.bat`. Mode kode ruang lokal di HP hanya dapat dipakai pada Wi-Fi yang sama; untuk teman di luar jaringan, gunakan URL hosting publik.
