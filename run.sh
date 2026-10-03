python3 -m pip install flask requests
pkill -f "python3 src/app.py"
python3 src/app.py &
PID=$!
#fuser -k 5000/tcp
sleep 1
xdg-open http://localhost:5000/
wait $PID