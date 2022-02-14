import $ from 'jquery';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js';
import { io } from 'socket.io-client'

const params = {
    fps: 60,
    exposure: 1,
    bloomStrength: 1.5,
    bloomThreshold: 0,
    bloomRadius: 0
};

let coords = [];
let colours = [];
let leds = [];

const socket = io.connect('http://localhost:5000');
socket.on('connect', function() {
    let colours_requested = false;
    socket.on('colour', (data) => {
        colours_requested = false;

        if (data) {
            data.forEach((pixel, pixelIndex) => {
                pixel.forEach((colour, colourIndex) => {
                    colours[pixelIndex][colourIndex] = colour;
                })
            })
            updateColours();
        }
    })

    function requestColours() {
        if (colours_requested === false) {
            colours_requested = true;
            socket.emit('colour');
        }
    }
    setInterval(requestColours, 1000/params.fps);
});

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera( 75, window.innerWidth / window.innerHeight, 0.1, 1000 );
const renderer = new THREE.WebGLRenderer({antialias: true});
const controls = new OrbitControls( camera, renderer.domElement );


renderer.setPixelRatio( window.devicePixelRatio );
renderer.setSize( window.innerWidth*0.99, window.innerHeight*0.98 );
renderer.toneMapping = THREE.ReinhardToneMapping;
document.body.appendChild( renderer.domElement );

const renderScene = new RenderPass( scene, camera );

const bloomPass = new UnrealBloomPass( new THREE.Vector2( window.innerWidth, window.innerHeight ), 1.5, 0.4, 0.85 );
bloomPass.threshold = params.bloomThreshold;
bloomPass.strength = params.bloomStrength;
bloomPass.radius = params.bloomRadius;

const composer = new EffectComposer( renderer );
composer.addPass( renderScene );
composer.addPass( bloomPass );

camera.position.z = 5;
controls.update();

function initLeds() {
    for (let i = 0; i < colours.length; i++) {
        const geometry = new THREE.SphereGeometry(1.5);
        const material = new THREE.MeshBasicMaterial({ color: `rgb(${colours[i][0]},${colours[i][1]},${colours[i][2]})` } );
        const led = new THREE.Mesh( geometry, material );
        led.position.set(coords[i][0]*100, coords[i][2]*100, coords[i][1]*100, )
        leds.push( led );
        scene.add( led );
    }
}

async function getState(url) {
    return $.ajax({
        url,
        type: 'GET',
        dataType: 'json'
    });
}

function animate() {
    requestAnimationFrame( animate );
    controls.update();
    composer.render();
}

function updateColours() {
    try {
        for (let i = 0; i < colours.length; i++) {
            let luminosity = (colours[i].reduce((partialSum, a) => partialSum+a, 0)) / (128*3);
            leds[i].scale.set(luminosity*1.5, luminosity*1.5, luminosity*1.5);
            leds[i].material.color.set(`rgb(${colours[i][0]},${colours[i][1]},${colours[i][2]})`);
        }
    } catch (err) {
        console.log(err);
    }
}

$(document).ready(() => {
    getState('http://localhost:5000/position').then((res) => {
        coords = res;
        return getState('http://localhost:5000/colour');
    }).then((res) => {
        colours = res;
        initLeds();

        animate();
    })
})
