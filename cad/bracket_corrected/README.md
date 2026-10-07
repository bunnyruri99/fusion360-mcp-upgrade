# Khung gá PCB TFT + ESP32-C3

Đây là bản sửa thay thế v1/v2/v3. Chỉ có hai chi tiết cần in:

- `frame.stl`: khung chính, đã gộp thành một solid.
- `rear_keeper.stl`: nẹp ESP32 tháo rời, đã gộp thành một solid.

`assembly.step` gồm khung, nẹp, ESP32 từ STEP thật, TFT dựng theo bản vẽ và vít/ê-cu minh họa. **Không in cả assembly.** `print_parts.step` chỉ có hai chi tiết khung/nẹp. Các file v1/v2/v3 bên ngoài thư mục này không dùng cho bản sửa.

## Lắp ráp

1. Đặt PCB TFT lên hai bệ tròn ở đầu có lỗ, mặt LCD hướng ra trước. Hai điểm đỡ ở đầu kia chỉ tì vào dải PCB ngoài mép LCD và nằm trước hàng header.
2. Bắt hai vít M2 qua hai lỗ sẵn Ø2,5 trên TFT và hai lỗ Ø2,2 trên khung. Tâm lỗ: (2,41; 2,41) và (18,67; 2,41) mm. Khoảng cách tâm 16,26 mm. Dùng hai ê-cu M2 phía sau. Model minh họa M2×8 cho PCB dày 1,6 mm; chọn chiều dài theo độ dày board thật.
3. Đặt ESP32 lên bốn điểm đỡ phía sau, mặt linh kiện hướng ra ngoài và USB-C hướng về đầu header của TFT. ESP32 song song TFT; hai mặt PCB gần nhau cách 11 mm.
4. Đặt nẹp cam từ phía sau ESP32. Bốn môi nẹp giữ góc PCB, gờ đầu/cạnh giới hạn dịch chuyển; nẹp không ép lên chip hay USB.
5. Bắt bốn vít M2×16 từ mặt sau nẹp xuyên bốn trụ, dùng bốn ê-cu M2 ở phía trước các trụ. Hai hàng chân ESP32 và lối USB-C để hở.

## Kích thước và kiểm tra

Solid PCB ESP32 trong file người dùng cung cấp: **17,8 × 22,7 × 0,9 mm**. Không dùng số 28,93 × 24 mm từng đo sai bằng cách quét mọi Cartesian point của STEP.

Khung rộng khoảng 28,9 mm. Khung và nẹp được kiểm tra mỗi chi tiết là một solid hợp lệ; STL kín và có một thành phần nối liền. Kiểm tra giao thể tích với STEP ESP32, PCB/LCD TFT giả lập, vùng header và đường tiếp cận USB cho kết quả 0. Chi tiết kết quả: `verification.json`.

**Chưa xác nhận lắp thực tế.** Bản vẽ TFT không cung cấp độ dày PCB/LCD hoặc linh kiện mặt sau. TFT trong assembly là mẫu kích thước: PCB tạm lấy 1,6 mm, LCD tạm lấy 1,5 mm. Hai điểm đỡ TFT đầu header cần đối chiếu mặt sau PCB thật. Độ kẹp ESP32 theo PCB 0,9 mm của STEP; dung sai in cần kiểm tra bằng bản in thử trước khi in nhiều.

Nguồn CAD: `../build_bracket.py`. Hình `preview.png` render từ chính model CAD, không phải ảnh tạo bằng AI. ESP STEP nhập qua [CadQuery STEP importer](https://cadquery.readthedocs.io/en/latest/importexport.html#importing-step).
