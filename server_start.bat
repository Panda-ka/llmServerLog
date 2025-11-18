@echo off
:: Initialize Conda environment (adjust path if necessary)
call activate llmLogServer

:: If the above doesn't work, try using the full path to activate.bat, for example:
:: call C:\Users\YourName\anaconda3\Scripts\activate.bat llmLogServer

:: Run the Python script
python llm_prompts_log_server.py

:: Keep the window open after execution (optional, useful for viewing output)
pause