python3 -m pip install flask requests
pkill -f "python3 src/app.py"
python3 src/app.py &
PID=$!
sleep 1
xdg-open http://localhost:5000/
wait $PID