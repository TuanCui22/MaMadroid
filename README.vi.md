# MaMaDroid — trích đặc trưng hành vi APK Android bằng chuỗi Markov

Biến một APK thành một vector số có kích thước cố định bằng cách đi qua call graph
của nó và ghi lại trạng thái API trừu tượng nào chuyển sang trạng thái nào. Vector
đó là thứ một classifier dùng; repo này tạo ra vector, không phải classifier.

Đây là bản fork được bảo trì của mã phát hành kèm bài báo NDSS 2017
*MaMaDroid: Detecting Android Malware by Building Markov Chains of Behavioral
Models* (Graziano, Canali, Bilge, Rao, Balzarotti). Phương pháp là của họ. Phần
đóng gói, xử lý đường dẫn và tối ưu ma trận là của bản fork này.

---

## Bản 2.0 khác gì bản 1.x

Mã 1.x chỉ chạy được trên đúng một máy, và README bảo bạn cài `requirements.txt`
trong khi file đó không tồn tại.

| Bản 1.x | Bản 2.0 |
|---|---|
| ba đường dẫn tuyệt đối `C:\Users\thanh\...` nằm trong `mamadroid_main` | mọi đường dẫn giải từ thư mục package, ghi đè được bằng biến môi trường `MAMADROID_*` |
| README nhắc `requirements.txt` nhưng file không có | dependency khai trong `pyproject.toml` |
| `python mamadroid.py -f … -d …` | `mamadroid -i … -o …`, thêm `--json` cho đầu ra máy đọc |
| vòng lặp Python ba lớp cho mỗi app | `numpy.add.at` scatter-add; cùng ma trận, có test so với thuật toán cũ |
| `except Exception` + ghi log, exit 0 | mỗi stage có danh sách lỗi riêng, exit code phản ánh đúng |
| CSV ghi bằng `','.join` | `csv.writer` — tên file có dấu phẩy không còn làm hỏng dòng |
| import trần (`from gml2txt import …`) | import tương đối kèm fallback cho chế độ chạy script |
| `--help` hỏng nếu chưa cài igraph | import nặng được làm lazy; `--help` và `--version` chạy được trên Python trơn |
| đọc lại file log rồi in | log ghi ra file và stderr, một lần |

Thay đổi đáng kể nhất về tốc độ là phần dựng ma trận. Bản gốc, với mỗi lời gọi
trong mỗi app, chạy vòng lặp lồng nhau trên toàn bộ không gian trạng thái. Với vài
nghìn APK và bộ từ vựng 400 trạng thái, đó là hàng chục triệu vòng lặp thông dịch.
Bản mới mã hoá một lần, scatter-add một lần, chuẩn hoá một lần — và có test khẳng
định nó cho ra đúng ma trận như vòng lặp cũ, nên tốc độ tăng không phải là thay
đổi hành vi.

---

## Cài đặt

```bash
git clone https://github.com/TuanCui22/MaMadroid.git
cd MaMadroid
python -m pip install -e .
```

Các stage phân tích còn cần JVM và `apktool` trên `PATH` (stage APK → call graph
gọi ra ngoài). `python -m pip install -e ".[dev]"` cài thêm công cụ test.

## Dùng

```bash
mamadroid -i /path/to/apks -o /path/to/output
```

| cờ | ý nghĩa |
|---|---|
| `-i, --input DIR` | thư mục chứa file `.apk` cần phân tích |
| `-o, --output DIR` | nơi ghi graph, chuỗi lời gọi và CSV đặc trưng |
| `-m, --mode MODE` | `Families`, `Packages` hoặc `Classes`; lặp lại được. Mặc định: Families và Packages |
| `--data-dir DIR` | nơi chứa `classes.txt`, `Packages.txt`, `Families11.txt` |
| `--memory SIZE` | heap JVM cho công cụ APK, ví dụ `2G` |
| `--json` | in tóm tắt lượt chạy dạng JSON thay vì text |

Exit code: `0` sạch, `1` có stage lỗi, `2` đường dẫn sai, `3` thiếu file tham
chiếu hoặc thiếu dependency.

### Nó tạo ra gì

```
output/
  MaMadroid/
    run.log              từng stage, từng file, có timestamp
    gml/                 một call graph cho mỗi APK
    graphs/Trial1/       một chuỗi caller→callee cho mỗi APK
    Features/
      Families/result.csv
      Packages/result.csv
```

Mỗi `result.csv` có một dòng cho mỗi APK: `filename`, rồi mỗi cặp `stateAToB` một
cột. Tập cột được cố định bởi danh sách tham chiếu, nên các dòng giữa các lần chạy
khác nhau vẫn thẳng hàng.

## Dữ liệu tham chiếu

Bộ từ vựng trạng thái đến từ ba danh sách đi kèm package: `classes.txt`,
`Packages.txt`, `Families11.txt`. Hai trạng thái tổng hợp (`self-defined`,
`obfuscated`) được thêm vào, khớp với bộ đặc trưng đã công bố — một model huấn
luyện trên đặc trưng của bài báo cần các cột đó tồn tại.

Nếu dữ liệu tham chiếu nằm chỗ khác:

```bash
export MAMADROID_DATA_DIR=/data/mamadroid
# hoặc từng file:
export MAMADROID_PACKAGES=/data/mamadroid/Packages.txt
```

Thiếu file tham chiếu sẽ được báo đúng tên kèm biến cần đặt, ngay đầu lượt chạy —
không phải `FileNotFoundError` sau hai mươi phút chuyển đổi APK.

## Kiểm thử

```bash
python -m pytest -q          # 14 test, không cần APK, không cần Java, không cần mạng
```

Bộ test phủ phần dựng ma trận (gồm so sánh với thuật toán vòng lặp gốc), trường
hợp dòng toàn số 0, xử lý nhãn lạ, việc quote CSV, cô lập lỗi từng app, và phần
giải đường dẫn từng bị hard-code.

## Cấu trúc

```
MAMADROID/MaMadroid/MaMadroid/
  cli.py               parse tham số, exit code
  mamadroid.py         pipeline: apk → gml → txt → abstract → features
  paths.py             mọi đường dẫn, giải một lần, ghi đè bằng env
  Markov.py            ma trận chuyển trạng thái (đã vector hoá)
  markov_processor.py  lắp ma trận đặc trưng và ghi CSV
  abstractGraph.py     ánh xạ lời gọi → trạng thái trừu tượng
  apk2graph.py         APK → call graph
  gml2txt.py           graph → chuỗi caller/callee
  parse.py             parse nhãn
  FamilytoMak.py       driver family-mode độc lập (legacy)
  PackagetoMak.py      driver package-mode độc lập (legacy)
  tests/test_markov.py
```

`FamilytoMak.py` và `PackagetoMak.py` là driver độc lập gốc, giữ lại vì các bước
tái lập của bài báo có nhắc tới. Lệnh `mamadroid` làm đúng việc đó nhưng với phần
xử lý đường dẫn không phụ thuộc máy.

## Trích dẫn

> MaMaDroid: Detecting Android Malware by Building Markov Chains of Behavioral Models
> Mariano Graziano, Davide Canali, Leyla Bilge, Ashwin Rao, Davide Balzarotti
> NDSS 2017

## Giấy phép

Artefact nghiên cứu riêng. Không phải open source, không phân phối lại. Xem
[`LICENSE`](LICENSE) và [`NOTICE`](NOTICE).
