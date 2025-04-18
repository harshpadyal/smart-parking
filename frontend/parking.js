const video = document.createElement('video');
video.id = 'cameraFeed';
video.style.position = 'absolute';
video.style.top = '50%';
video.style.left = '50%';
video.style.transform = 'translate(-50%, -50%)';
video.style.width = '50%';
video.style.zIndex = '1000';
video.style.display = 'none';
video.autoplay = true; // Ensure webcam starts
document.body.appendChild(video);

const canvas = document.createElement('canvas');
canvas.style.display = 'none';
document.body.appendChild(canvas);

const scanFrame = document.createElement('div');
scanFrame.id = 'scanFrame';
scanFrame.style.position = 'absolute';
scanFrame.style.border = '2px dashed red';
scanFrame.style.width = '60%';
scanFrame.style.height = '30%';
scanFrame.style.top = '50%';
scanFrame.style.left = '50%';
scanFrame.style.transform = 'translate(-50%, -50%)';
scanFrame.style.zIndex = '1001';
scanFrame.style.display = 'none';
document.body.appendChild(scanFrame);

var w, h;
var parklock = false;
var parklist = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
var queueitems = 0;

function setupparkingmanager() {
    w = document.getElementById('parkingspace').offsetWidth;
    h = document.getElementById('parkingspace').offsetHeight;

    var anim = document.createElement('style');
    var rule1 = document.createTextNode('@-webkit-keyframes car-park {' +
        'from { transform: rotate(270deg); }' +
        '80% { transform: rotate(270deg) translate(0px, -' + w + 'px); }' +
        '90% { transform: rotate(270deg) translate(0px, -' + w + 'px) rotate(90deg); }' +
        'to { transform: rotate(270deg) translate(0px, -' + w + 'px) rotate(90deg) translate(0px, -' + h * .25 + 'px); }' +
        '}');
    anim.appendChild(rule1);
    var rule2 = document.createTextNode('@-webkit-keyframes car-bottom {' +
        'from { transform: rotate(270deg); }' +
        '80% { transform: rotate(270deg) translate(0px, -' + w + 'px); }' +
        '90% { transform: rotate(270deg) translate(0px, -' + w + 'px) rotate(90deg); }' +
        'to { transform: rotate(270deg) translate(0px, -' + w + 'px) rotate(90deg) translate(0px, ' + h * .25 + 'px); }' +
        '}');
    anim.appendChild(rule2);
    var rule3 = document.createTextNode('@-webkit-keyframes car-exit-top {' +
        'from { transform: rotate(270deg) translate(0px, -' + w + 'px) rotate(90deg) translate(0px, -' + h * .25 + 'px); }' +
        '80% { transform: rotate(270deg) translate(0px, -' + w + 'px) rotate(90deg) translate(0px, -' + h * .25 + 'px) translate(0px, ' + h * .25 + 'px); }' +
        '90% { transform: rotate(270deg) translate(0px, -' + w + 'px) rotate(90deg) translate(0px, -' + h * .25 + 'px) translate(0px, ' + h * .25 + 'px) rotate(90deg); }' +
        'to { transform: rotate(270deg) translate(0px, -' + w + 'px) rotate(90deg) translate(0px, -' + h * .25 + 'px) translate(0px, ' + h * .25 + 'px) rotate(90deg) translate(0px, -' + w + 'px); }' +
        '}');
    anim.appendChild(rule3);
    var rule4 = document.createTextNode('@-webkit-keyframes car-exit-bottom {' +
        'from { transform: rotate(270deg) translate(0px, -' + w + 'px) rotate(90deg) translate(0px, ' + h * .25 + 'px); }' +
        '80% { transform: rotate(270deg) translate(0px, -' + w + 'px) rotate(90deg) translate(0px, ' + h * .25 + 'px) translate(0px, -' + h * .25 + 'px); }' +
        '90% { transform: rotate(270deg) translate(0px, -' + w + 'px) rotate(90deg) translate(0px, ' + h * .25 + 'px) translate(0px, -' + h * .25 + 'px) rotate(90deg); }' +
        'to { transform: rotate(270deg) translate(0px, -' + w + 'px) rotate(90deg) translate(0px, ' + h * .25 + 'px) translate(0px, -' + h * .25 + 'px) rotate(90deg) translate(0px, -' + w + 'px); }' +
        '}');
    anim.appendChild(rule4);
    document.getElementById('parkingspace').appendChild(anim);

    // Fetch parking state on load
    fetchParkingState();
}

function fetchParkingState() {
    fetch('http://localhost:5000/get_parking_state', {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => { throw err; });
        }
        return response.json();
    })
    .then(data => {
        console.log("Fetched parking state:", data);
        parklist = data.parklist;
        data.parked_slots.forEach(slot => {
            if (parklist[slot.slot] === 1) {
                generatenewcar(slot.slot);
                document.getElementById('slot' + (slot.slot + 1).toString()).style.background = 'rgb(146,18,18)';
                const car = document.getElementById('car' + slot.slot.toString());
                if (slot.slot != 4 && slot.slot != 9)
                    car.style.right = (-w + (w * .1) + (((5 - (slot.slot + 1) % 5)) * ((w * .8) * .2)) + ((w * .8) * .05)) + 'px';
                else
                    car.style.right = (-w + (w * .1) + ((w * .8) * .05)) + 'px';
                car.style.transform = slot.slot <= 4
                    ? `rotate(270deg) translate(0px, -${w}px) rotate(90deg) translate(0px, -${h * .25}px)`
                    : `rotate(270deg) translate(0px, -${w}px) rotate(90deg) translate(0px, ${h * .25}px)`;
            }
        });
        console.log("Updated parklist:", parklist);
    })
    .catch(err => {
        console.error("Error fetching parking state:", err);
        alert("Failed to load parking state: " + (err.error || "Unknown error"));
    });
}

function updatequeue() {
    for (let i = 1; i <= 5; i++) {
        if (i <= queueitems) {
            document.getElementById('queue' + i.toString()).src = 'car.png';
        } else {
            document.getElementById('queue' + i.toString()).src = 'carfaded.png';
        }
    }
}

function addtoqueue() {
    var freeslotflag = 0;
    for (let j = 0; j < 10; j++) {
        if (parklist[j] != 1) {
            freeslotflag = 1;
            alert("Free slots available");
            break;
        }
    }
    if (freeslotflag != 1) {
        queueitems = queueitems + 1;
        if (queueitems > 5)
            alert("Queue Limit Reached");
        else
            updatequeue();
    }
}

function queuecheck(slot) {
    if (queueitems > 0) {
        queueitems = queueitems - 1;
        updatequeue();
        carenter(slot);
    }
}

function carexit(slot) {
    if (!parklock) {
        parklock = true;
        console.log("Attempting to exit slot:", slot);
        fetch('http://localhost:5000/exit_vehicle', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ slot: slot })
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => { throw err; });
            }
            return response.json();
        })
        .then(data => {
            parklist[slot] = 0;
            console.log(parklist);
            document.getElementById('slot' + (slot + 1).toString()).style.background = 'rgb(27,118,19)';
            if (slot <= 4)
                document.getElementById('car' + slot.toString()).style.animation = 'car-exit-top 2s both';
            else
                document.getElementById('car' + slot.toString()).style.animation = 'car-exit-bottom 2s both';
            setTimeout(function() {
                document.getElementById('car' + slot.toString()).remove();
                parklock = false;
                queuecheck(slot);
                alert("Vehicle exited: " + data.plate_number + " from slot " + (slot + 1));
            }, 2000);
        })
        .catch(err => {
            console.error("Exit error:", err);
            parklock = false;
            alert("Error during exit: " + (err.error || "Unknown error"));
        });
    }
}

function generatenewcar(slot) {
    var space = document.getElementById('parkingspace');
    let img = document.createElement('img');
    img.src = 'car.png';
    img.className = 'new-car-origin';
    img.style.width = (w * .8) * .1 + 'px';
    img.id = 'car' + slot.toString();
    space.appendChild(img);
}

function carenter(slot) {
    console.log("carenter called for slot:", slot);
    if (!document.getElementById('car' + slot.toString()) && !parklock) {
        navigator.mediaDevices.getUserMedia({ video: true })
            .then(stream => {
                console.log("Webcam stream obtained:", stream);
                video.srcObject = stream;
                video.style.display = 'block';
                scanFrame.style.display = 'block';
                video.play().then(() => {
                    console.log("Webcam playing");
                }).catch(err => {
                    console.error("Play error:", err);
                });

                let isProcessing = false;
                function processFrame() {
                    if (isProcessing || !video.srcObject) return;
                    isProcessing = true;

                    canvas.width = video.videoWidth;
                    canvas.height = video.videoHeight;
                    const context = canvas.getContext('2d');
                    context.drawImage(video, 0, 0, canvas.width, canvas.height);

                    const imageData = canvas.toDataURL('image/jpeg');
                    fetch('http://localhost:5000/process_license_plate', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ image: imageData, slot: slot })
                    })
                    .then(response => {
                        if (!response.ok) {
                            return response.json().then(err => { throw err; });
                        }
                        return response.json();
                    })
                    .then(data => {
                        stream.getTracks().forEach(track => track.stop());
                        video.style.display = 'none';
                        scanFrame.style.display = 'none';

                        if (data.error) {
                            alert("Error: " + data.error + (data.plate_number ? " (" + data.plate_number + ")" : ""));
                            isProcessing = false;
                        } else {
                            parklist[slot] = 1;
                            console.log(parklist);
                            parklock = true;
                            generatenewcar(slot);
                            document.getElementById('slot' + (slot + 1).toString()).style.background = 'rgb(146,18,18)';
                            if (slot != 4 && slot != 9)
                                document.getElementById('car' + slot.toString()).style.right = (-w + (w * .1) + (((5 - (slot + 1) % 5)) * ((w * .8) * .2)) + ((w * .8) * .05)) + 'px';
                            else
                                document.getElementById('car' + slot.toString()).style.right = (-w + (w * .1) + ((w * .8) * .05)) + 'px';
                            if (slot <= 4)
                                document.getElementById('car' + slot.toString()).style.animation = 'car-park 2s both';
                            else
                                document.getElementById('car' + slot.toString()).style.animation = 'car-bottom 2s both';
                            setTimeout(function() { parklock = false; }, 2000);
                            alert("Vehicle parked: " + data.plate_number + " at slot " + (slot + 1));
                        }
                    })
                    .catch(err => {
                        console.error("Error:", err);
                        if (err.error === "Not registered license plate") {
                            stream.getTracks().forEach(track => track.stop());
                            video.style.display = 'none';
                            scanFrame.style.display = 'none';
                            alert("Not registered license plate: " + err.plate_number);
                        } else {
                            isProcessing = false;
                            requestAnimationFrame(processFrame);
                        }
                    });
                }

                requestAnimationFrame(processFrame);
            })
            .catch(err => {
                console.error("Error accessing camera:", err);
                alert("Camera access denied. Please allow camera permissions.");
            });
    } else {
        carexit(slot);
    }
}

function captureAndProcess(slot, stream) {
    // Kept for reference, not used
}

function sendToBackend(imageData, slot) {
    // Kept for reference, not used
}