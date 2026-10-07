# Khung và case TFT 2,25 inch + ESP32-C3 SuperMini

Bản này được dựng bằng sketch, extrude và cut trực tiếp trong Fusion. ESP dùng mô hình STEP người dùng cung cấp, xoay song song sau TFT và đưa USB ra đầu ngắn gần hai lỗ bắt màn hình.

## Kích thước

- Case ngoài: 33,98 × 78,55 × 18,9 mm, thành chính 2 mm.
- Khoảng cách giữa mặt sau PCB TFT và mặt PCB ESP gần TFT: 6,2 mm.
- Miệng USB: 9,6 × 3,8 mm, góc R1,8; dư 0,3 mm quanh vỏ kim loại trong STEP.
- Mặt kim loại cổng USB lùi 0,25 mm so với mặt ngoài case.
- Hai hốc ê-cu M2 dưới khung: rộng qua hai mặt phẳng 4,2 mm, sâu 1,75 mm.

## Các phần in

1. `01_KHUNG_HA_ESP.stl`: khung chính, đỡ TFT và PCB ESP.
2. `02_NEP_ESP.stl`: nẹp tháo được, chặn các góc PCB ESP và chừa vùng linh kiện.
3. `03_THAN_CASE.stl`: thân case, cửa sổ màn hình, lỗ USB và trụ bắt vít.
4. `04_NAP_SAU.stl`: nắp sau, gờ định vị và hốc đầu vít.

STL xuất từ Fusion theo mm; mỗi file là một khối kín liền nhau.

## Thứ tự lắp

1. Đặt hai ê-cu M2 vào hốc phía sau khung. Đặt TFT lên mặt trước, bắt hai vít M2 × 6 qua hai lỗ PCB vào ê-cu. Đầu trên PCB tựa hai mép đỡ, không tì vào kính LCD.
2. Đặt ESP vào bốn mặt tựa dưới khung, USB hướng về đầu ngắn gần hai lỗ TFT. Úp nẹp sau ESP và bắt bốn vít M2 × 6 qua nẹp vào các lỗ mồi Ø1,7 của khung. Nẹp giữ PCB bằng các mép, không cần khoan board ESP.
3. Hàn và đi dây trong khoảng trống giữa hai PCB, hướng bó dây về đầu 8 chân TFT. Kiểm tra đầu USB cắm được trước khi đóng nắp.
4. Đưa cụm TFT–khung–ESP vào thân từ phía sau. Canh USB với lỗ đầu ngắn, bắt bốn vít M2 × 6 qua khung vào bốn trụ phía trước của case.
5. Đặt nắp sau theo gờ định vị, bắt bốn vít M2 × 6 vào bốn trụ còn lại. Tổng dự kiến: 14 vít M2 × 6 và hai ê-cu M2; kiểm tra chiều cao đầu vít thực tế với các hốc.

## Những kích thước còn cần đối chiếu

PCB TFT dày 1,6 mm và cụm LCD nhô thêm 1,5 mm đang là giả định, tổng 3,1 mm. Khoảng nhô của hàng chân TFT phía sau đang giả định 6 mm. STEP ESP không có hàng pin đã hàn. Độ dày màn thật, dây và mối hàn có thể yêu cầu chỉnh khoang trước bản in cuối.

Kiểm tra CAD: bốn chi tiết nhựa là solid liền, không giao thể tích với nhau hoặc với STEP ESP và mô hình TFT tham chiếu. Đây là kiểm tra hình học; độ ôm PCB và lỗ mồi vít vẫn cần lắp thử chi tiết in.
