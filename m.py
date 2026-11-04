import msvcrt
import os
import random
import time

LEBAR = 30
TINGGI = 15
JEDA = 0.12


def buat_makanan(ular1, ular2):
    kosong = [
        (x, y)
        for y in range(TINGGI)
        for x in range(LEBAR)
        if (x, y) not in ular1 and (x, y) not in ular2
    ]
    return random.choice(kosong) if kosong else None


def baca_tombol(arah1, arah2, belok1, belok2):
    tombol_arah = {
        "w": (0, -1), "s": (0, 1),
        "a": (-1, 0), "d": (1, 0),
    }
    panah_arah = {
        b"H": (0, -1),  # atas
        b"P": (0, 1),   # bawah
        b"K": (-1, 0),  # kiri
        b"M": (1, 0),   # kanan
    }

    while msvcrt.kbhit():
        tombol = msvcrt.getch()
        arah_baru = None
        pemain = None

        if tombol in (b"\x00", b"\xe0"):
            arah_baru = panah_arah.get(msvcrt.getch())
            pemain = 2
        else:
            karakter = tombol.decode("utf-8", errors="ignore").lower()
            arah_baru = tombol_arah.get(karakter)
            pemain = 1

        if arah_baru is None:
            continue

        if pemain == 1 and not belok1:
            if arah_baru != (-arah1[0], -arah1[1]):
                arah1 = arah_baru
                belok1 = True
        elif pemain == 2 and not belok2:
            if arah_baru != (-arah2[0], -arah2[1]):
                arah2 = arah_baru
                belok2 = True

    return arah1, arah2, belok1, belok2


def gambar(ular1, ular2, makanan, skor1, skor2):
    papan = [[" " for _ in range(LEBAR)] for _ in range(TINGGI)]

    if makanan is not None:
        x, y = makanan
        papan[y][x] = "*"

    for x, y in ular1[1:]:
        papan[y][x] = "1"
    for x, y in ular2[1:]:
        papan[y][x] = "2"

    x, y = ular1[0]
    papan[y][x] = "A"
    x, y = ular2[0]
    papan[y][x] = "B"

    os.system("cls")
    print(f"ULAR 2 PEMAIN    Pemain 1: {skor1}    Pemain 2: {skor2}")
    print("Pemain 1: WASD | Pemain 2: tombol panah | Ctrl+C untuk keluar")
    print("+" + "-" * LEBAR + "+")
    for baris in papan:
        print("|" + "".join(baris) + "|")
    print("+" + "-" * LEBAR + "+")


def main():
    ular1 = [(5, 7), (4, 7), (3, 7)]
    ular2 = [(24, 7), (25, 7), (26, 7)]
    arah1 = (1, 0)
    arah2 = (-1, 0)
    skor1 = 0
    skor2 = 0
    makanan = buat_makanan(ular1, ular2)

    while True:
        gambar(ular1, ular2, makanan, skor1, skor2)
        belok1 = False
        belok2 = False
        arah1, arah2, belok1, belok2 = baca_tombol(
            arah1, arah2, belok1, belok2
        )

        kepala1 = (ular1[0][0] + arah1[0], ular1[0][1] + arah1[1])
        kepala2 = (ular2[0][0] + arah2[0], ular2[0][1] + arah2[1])
        makan1 = kepala1 == makanan
        makan2 = kepala2 == makanan

        def menabrak(kepala, sendiri, lawan, lawan_makan):
            x, y = kepala
            if not (0 <= x < LEBAR and 0 <= y < TINGGI):
                return True

            badan_sendiri = sendiri if kepala == makanan else sendiri[:-1]
            badan_lawan = lawan if lawan_makan else lawan[:-1]
            return kepala in badan_sendiri or kepala in badan_lawan

        tabrak1 = menabrak(kepala1, ular1, ular2, makan2)
        tabrak2 = menabrak(kepala2, ular2, ular1, makan1)

        if kepala1 == kepala2 or (kepala1 == ular2[0] and kepala2 == ular1[0]):
            tabrak1 = True
            tabrak2 = True

        if tabrak1 or tabrak2:
            break

        ular1.insert(0, kepala1)
        ular2.insert(0, kepala2)

        if makan1:
            skor1 += 1
        else:
            ular1.pop()

        if makan2:
            skor2 += 1
        else:
            ular2.pop()

        if makan1 or makan2:
            makanan = buat_makanan(ular1, ular2)
            if makanan is None:
                break

        time.sleep(JEDA)

    gambar(ular1, ular2, makanan, skor1, skor2)
    print("\nPermainan selesai!")
    if tabrak1 and tabrak2:
        print("Seri! Kedua pemain menabrak.")
    elif tabrak1:
        print("Pemain 2 menang!")
    elif tabrak2:
        print("Pemain 1 menang!")
    else:
        print("Papan penuh!")
        if skor1 > skor2:
            print("Pemain 1 menang!")
        elif skor2 > skor1:
            print("Pemain 2 menang!")
        else:
            print("Skor seri!")


if __name__ == "__main__":
    main()