# STM32 Mass Programmer ⚡

Batch flashing tool for STM32 devices using STM32CubeProgrammer CLI.

---

🛠️ PREREQUISITES
------------------------------
1. STM32CubeProgrammer Installed </br>
   ➤ Download: https://www.st.com/en/development-tools/stm32cubeprog.html </br>
   ➤ Recommended Version: 2.15.0 or newer

3. Add STM32CubeProgrammer to System PATH:</br>
   ➤ Default path:</br>
     C:\Program Files\STMicroelectronics\STM32Cube\STM32CubeProgrammer\bin</br>

   ➤ To add it to PATH:</br>
     1. Press Win + R, type: sysdm.cpl</br>
     2. Go to "Advanced" → Environment Variables</br>
     3. Edit the "Path" variable → Add the path above

---

🚀 INSTALLATION
------------------------------

Method 1: Pre-built Executable
   1. Download the latest STM32_Mass_Programmer.exe from Releases
   2. Run the executable

Method 2: From Python Source
   1. git clone https://github.com/yourusername/STM32_Mass_Programmer.git
   2. cd STM32_Mass_Programmer
   3. ```sudo apt install python3-tk```
   4. python HMI_Flasher.py

---

🖥️ USAGE GUIDE
------------------------------

➤ Step 1: File Selection
   - Browse and select your firmware .hex file
   - Loader path: Browse or use default (.stldr)
   - Click "Next ➡"

➤ Step 2: Device Management

| Column         | Description                              |
|----------------|------------------------------------------|
| ST-Link Serial | ST-Link programmer serial number         |
| Device ID      | MCU ID (e.g., 0xABCD) or "No target"     |
| Status         | ✅ Ready / 🔄 Flashing / ❌ Disconnected |
| Time           | Flashing time elapsed                    |
| Action         | Upload button for flashing               |

Buttons:
   🔄 Refresh – Re-scan for ST-Links  
   ⬆ Upload – Start flashing a selected device

---

🔄 FLASHING PROCESS
------------------------------
1. Click Upload for a device</br>
2. You’ll see real-time progress:</br>
   - "Erasing..."
   - "Flashing..."
   - "Verifying..."
3. Final status:</br>
   ✅ Flashing Success</br>
   ❌ Flashing Failed (check logs)

---

⚠️ TROUBLESHOOTING
------------------------------

❌ Device Not Detected:
   - Check USB cable & connections 
   - Try different USB port 
   - Ensure ST-Link drivers are installed 

❌ "STM32_Programmer_CLI not found":
   - Ensure STM32CubeProgrammer 'bin' folder is in your PATH </br>

❌ Flashing Fails:
| Error                      | Possible Fixes                                     |
|----------------------------|----------------------------------------------------|
| "Timeout"                  | 1. Increase TIMEOUT_PER_DEVICE in code            |
|                            | 2. Check if device is powered and responsive      |
| "Verification failed"      | 1. Use correct external loader (.stldr)           |
|                            | 2. Verify target voltage & board connection       |
| "Port SWD not found"       | 1. Reset target board                             |
|                            | 2. Reconnect USB / try different port             |

📝 LOGS
------------------------------
• Detailed flashing logs saved in:
  → stm32_programmer_debug.log

📁 CHOOSING THE CORRECT LOADER (.stldr)
-----------------------------------------------

STM32 devices that use external Flash (like QSPI or OSPI) require a special "external loader" file
with a `.stldr` extension to allow flashing using STM32CubeProgrammer.

💡 What is it?
→ A `.stldr` file tells STM32CubeProgrammer how to access your board’s external memory.

✅ How to Choose the Correct Loader:</br>

1. 🔍 Identify Your Flash Chip:</br>
   • Check your board schematic or Flash chip marking</br>
   • Example: Macronix MX66UW1G45G</br>

2. 📌 Know Your Board/MCU:</br>
   • Example: STM32H7S78-DK (uses OctoSPI NOR Flash)</br>

3. 📂 Locate Loader File:</br>
   • Path:</br>
     ```C:\Program Files\STMicroelectronics\STM32Cube\STM32CubeProgrammer\bin\ExternalLoader\``` </br>
   • Look for a file that matches your board/chip </br>
     → Example: MX66UW1G45G_STM32H7S78-DK.stldr </br>

🛠️ If No Loader Exists:</br>
• You may need to create a custom loader using STM32CubeIDE</br>
• ST provides templates for building `.stldr` projects</br>

