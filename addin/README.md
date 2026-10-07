# Add-in Kurulum Kılavuzu

→ [INDEX](../INDEX.md)

## Kurulum (Windows)

1. `fusion360_mcp_bridge/` klasörünü kopyala:

```
Kaynak:  addin/fusion360_mcp_bridge/
Hedef:   %APPDATA%\Autodesk\Autodesk Fusion 360\API\AddIns\fusion360_mcp_bridge\
```

2. Fusion 360'ı aç (veya yeniden başlat)

3. **Tools → Add-Ins → Add-Ins** sekmesi (kısayol: `Shift+S`)

4. `fusion360_mcp_bridge` seç → **Run**

5. Ekranda **"Fusion MCP bridge started — listening on port 9876"** çık

6. Opsiyonel: **Run on Startup** işaretle

## Güncelleme

Add-in dosyasını değiştirdiğinde:
1. Fusion'da add-in'i **Stop** et
2. Dosyayı kopyala (üzerine yaz)
3. **Run** et

## Bağlantı Testi (PowerShell)

```powershell
$tcp = New-Object System.Net.Sockets.TcpClient
$tcp.Connect("127.0.0.1", 9876)
"Bağlantı başarılı"
$tcp.Close()
```

## Port Çakışması

9876 portu kullanımdaysa `.env` dosyasında değiştir:

```
FUSION_PORT=9877
```

Add-in içindeki `PORT = 9876` satırını da güncelle.
