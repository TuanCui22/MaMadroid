![BOLTER](docs/banner.svg)

# BOLTER

**Đặc trưng hành vi APK Android bằng chuỗi Markov.**

Biến một APK thành vector số có kích thước cố định bằng cách đi qua call graph của
nó và ghi lại trạng thái API trừu tượng nào chuyển sang trạng thái nào. Vector đó
là thứ classifier dùng; repo này tạo ra vector, không phải classifier.

Đây là bản fork được bảo trì của mã phát hành kèm bài báo NDSS 2017
*MaMaDroid: Detecting Android Malware by Building Markov Chains of Behavioral
Models* (Graziano, Canali, Bilge, Rao, Balzarotti). Phương pháp là của họ. Phần
đóng gói, xử lý đường dẫn và tối ưu ma trận là của bản fork này.

---


## Trông thế nào khi chạy

```
$ bolter --help
usage: bolter [-h] [--version] -i DIR -o DIR [-m MODE] [--data-dir DIR]
              [--memory SIZE] [--log-level LEVEL] [--json] [--report PATH]
              [--summary-in PATH]

  -i, --input DIR    directory containing the APK files to analyse
  -o, --output DIR   directory for graphs, sequences and feature CSVs
  -m, --mode MODE    feature mode; repeatable (default Families and Packages)
  --report PATH      also write a self-contained HTML run report
```

Một lượt chạy, một thư mục APK, một CSV cho mỗi mode. `--mode` lặp được, nên một
lần chạy có thể xuất cả ma trận `Families` và `Packages` thẳng hàng theo từng dòng.

`--report out.html` ghi một trang trả lời câu mà CSV không trả lời được: app nào
tạo ra dòng toàn số 0, tức là APK nào hỏng ở bước chuyển đổi phía trước. Không
server, không request ra ngoài.

## Năng lực

| | |
|---|---|
| **Ba chế độ trừu tượng** | `Families`, `Packages` và `Classes`, chọn theo từng lượt chạy và lặp lại được. Mỗi chế độ có bộ từ vựng trạng thái riêng. |
| **Dựng ma trận đã vector hoá** | Chuyển trạng thái được tích luỹ bằng một scatter-add trên mảng chỉ số, thay vì vòng lặp lồng nhau cho từng lời gọi. Có test khẳng định kết quả khớp chính xác với thuật toán tham chiếu. |
| **Đường dẫn di động** | Mọi đường dẫn giải từ thư mục package và ghi đè được bằng biến môi trường `MAMADROID_*`. Thiếu file tham chiếu sẽ được báo đúng tên ngay đầu lượt chạy. |
| **Cô lập từng app** | APK chuyển đổi lỗi sẽ được ghi nhận và bỏ qua; cả lô tiếp tục và exit code phản ánh điều đó. |
| **Đầu ra có cấu trúc** | Mỗi chế độ một CSV, mỗi APK một dòng, bộ cột cố định nên các dòng giữa các lần chạy thẳng hàng. `--json` cho máy đọc. |
| **Import phân tích lazy** | `--help` và `--version` chạy được trên Python trơn. Thiếu dependency phân tích sẽ báo đúng tên package và lệnh cài. |
| **Dòng rỗng trung thực** | Trạng thái không có chuyển tiếp đi ra vẫn là toàn số 0, không thành NaN — "chưa từng rời trạng thái này" và "trạng thái này không tồn tại" là hai sự kiện khác nhau. |
| **Báo cáo lượt chạy** | `--report out.html` ghi một trang tự chứa: số lượng từng stage, mật độ theo từng mode, và tên từng app tạo ra dòng toàn số 0. Không server, không request ra ngoài. |

---

## Cài đặt

```bash
git clone https://github.com/TuanCui22/bolter.git
cd bolter
python -m pip install -e .
```

Các stage phân tích còn cần JVM và `apktool` trên `PATH` (stage APK → call graph
gọi ra ngoài). `python -m pip install -e ".[dev]"` cài thêm công cụ test.

## Dùng

```bash
bolter -i /path/to/apks -o /path/to/output
```

| Cờ | Ý nghĩa |
|---|---|
| `-i, --input DIR` | thư mục chứa file `.apk` cần phân tích |
| `-o, --output DIR` | nơi ghi graph, chuỗi lời gọi và CSV đặc trưng |
| `-m, --mode MODE` | `Families`, `Packages` hoặc `Classes`; lặp lại được. Mặc định: Families và Packages |
| `--data-dir DIR` | nơi chứa `classes.txt`, `Packages.txt`, `Families11.txt` |
| `--memory SIZE` | heap JVM cho công cụ APK, ví dụ `2G` |
| `--json` | in tóm tắt lượt chạy dạng JSON thay vì text |
| `--report PATH` | ghi thêm báo cáo HTML tự chứa |
| `--summary-in PATH` | file summary JSON để nhúng vào báo cáo |
| `--log-level LEVEL` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |

Exit code: `0` sạch, `1` có stage lỗi, `2` đường dẫn sai, `3` thiếu file tham
chiếu hoặc thiếu dependency.

### Output

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
cột. Tập cột cố định bởi danh sách tham chiếu, nên các dòng giữa các lần chạy khác
nhau vẫn thẳng hàng.

## Dữ liệu tham chiếu

Bộ từ vựng trạng thái đến từ ba danh sách đi kèm package: `classes.txt`,
`Packages.txt`, `Families11.txt`. Hai trạng thái tổng hợp (`self-defined`,
`obfuscated`) được thêm vào, khớp với bộ đặc trưng đã công bố — một model huấn
luyện trên đặc trưng của bài báo cần các cột đó tồn tại.

Trỏ dữ liệu tham chiếu đi chỗ khác:

```bash
export MAMADROID_DATA_DIR=/data/mamadroid
# hoặc từng file:
export MAMADROID_PACKAGES=/data/mamadroid/Packages.txt
```

## Báo cáo lượt chạy

```bash
bolter -i /path/to/apks -o /path/to/output --report output/report.html
```

Một file HTML tự chứa: CSS nhúng, không script nào gọi ra ngoài, không mở port.
Trang trả lời ba câu theo đúng thứ tự người phân tích hỏi — lượt chạy có chạy
được không, ma trận có dùng được không, và app nào bị hỏng.

Câu thứ ba là điểm chính. Một dòng toàn số 0 không phải "không có đặc trưng": nó
nghĩa là app đó không tạo ra chuyển tiếp API nào, gần như luôn là do bước chuyển
đổi APK hỏng từ trước. Trang nêu tên các app đó thay vì để bạn tự diff CSV. Giá
trị không tính được hiện ra thành khoảng trống có tên, không bao giờ thành số 0.

Mỗi lượt chạy cũng ghi `MaMadroid/run-summary.json` cạnh thư mục output, để trang
và terminal hiện cùng một con số thay vì hai lần tính lại.

## Kiểm thử

```bash
python -m pytest -q          # 25 test, không cần APK, không cần Java, không cần mạng
```

Bộ test phủ phần dựng ma trận (so với thuật toán tham chiếu), trường hợp dòng toàn
số 0, xử lý nhãn lạ, việc quote CSV, cô lập lỗi từng app, và phần giải đường dẫn.

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
  FamilytoMak.py       driver family-mode độc lập
  PackagetoMak.py      driver package-mode độc lập
  tests/test_markov.py
```

`FamilytoMak.py` và `PackagetoMak.py` là các driver độc lập được nhắc tới trong
bước tái lập của bài báo. Lệnh `mamadroid` làm đúng việc đó với phần xử lý đường
dẫn di động.

## Trích dẫn

> MaMaDroid: Detecting Android Malware by Building Markov Chains of Behavioral Models
> Mariano Graziano, Davide Canali, Leyla Bilge, Ashwin Rao, Davide Balzarotti
> NDSS 2017

## Giấy phép

Artefact nghiên cứu riêng. Không phải open source, không phân phối lại. Xem
[`LICENSE`](LICENSE) và [`NOTICE`](NOTICE).
