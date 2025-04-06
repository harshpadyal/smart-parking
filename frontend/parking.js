const video = document.createElement('video');
video.id = 'cameraFeed';
video.style.position = 'absolute'; // Position it over the UI
video.style.top = '50%'; // Center vertically
video.style.left = '50%'; // Center horizontally
video.style.transform = 'translate(-50%, -50%)'; // Center adjustment
video.style.width = '50%'; // Adjust size as needed
video.style.zIndex = '1000'; // Ensure it’s on top
video.style.display = 'none'; // Hidden initially
document.body.appendChild(video);

const canvas = document.createElement('canvas');
canvas.style.display = 'none';
document.body.appendChild(canvas);

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
        parklist[slot] = 0;
        console.log(parklist);
        parklock = true;
        document.getElementById('slot' + (slot + 1).toString()).style.background = 'rgb(27,118,19)';
        if (slot <= 4)
            document.getElementById('car' + slot.toString()).style.animation = 'car-exit-top 2s both';
        else
            document.getElementById('car' + slot.toString()).style.animation = 'car-exit-bottom 2s both';
        setTimeout(function() {
            document.getElementById('car' + slot.toString()).remove();
            parklock = false;
            queuecheck(slot);
        }, 2000);
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
    if (!document.getElementById('car' + slot.toString()) && !parklock) {
        navigator.mediaDevices.getUserMedia({ video: true })
            .then(stream => {
                video.srcObject = stream;
                video.style.display = 'block'; // Show the video feed
                video.play();
                
                // Create a capture button
                const captureButton = document.createElement('button');
                captureButton.textContent = 'Capture License Plate';
                captureButton.style.position = 'absolute';
                captureButton.style.top = '70%';
                captureButton.style.left = '50%';
                captureButton.style.transform = 'translate(-50%, -50%)';
                captureButton.style.zIndex = '1001';
                document.body.appendChild(captureButton);

                captureButton.onclick = () => {
                    captureAndProcess(slot, stream);
                    video.style.display = 'none'; // Hide video after capture
                    captureButton.remove(); // Remove button
                };
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
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const context = canvas.getContext('2d');
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    stream.getTracks().forEach(track => track.stop());

    const imageData = canvas.toDataURL('image/jpeg');
    sendToBackend(imageData, slot);
}

function sendToBackend(imageData, slot) {
    fetch('http://localhost:5000/process_license_plate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image: imageData, slot: slot })
    })
    .then(response => response.json())
    .then(data => {
        if (data.plate_number) {
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
            alert("License plate stored: " + data.plate_number);
        } else {
            alert("Failed to process license plate: " + data.error);
        }
    })
    .catch(err => {
        console.error("Error sending to backend:", err);
        alert("Error connecting to server.");
    });
}