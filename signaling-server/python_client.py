#!/usr/bin/env python3
"""
Cliente WebRTC Python com OpenCV
Captura vídeo da câmera e estabelece conexão P2P
"""

import asyncio
import json
import logging
import cv2
import numpy as np
import websockets
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceCandidate, VideoStreamTrack
from aiortc.contrib.signaling import BYE
import threading
import time
from typing import Optional
import signal
import sys

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CameraVideoStreamTrack(VideoStreamTrack):
    """
    Track de vídeo que captura da câmera usando OpenCV
    """
    def __init__(self, camera_id: int = 0):
        super().__init__()
        self.camera_id = camera_id
        self.cap = None
        self._start_camera()
    
    def _start_camera(self):
        """Inicia a captura da câmera"""
        self.cap = cv2.VideoCapture(self.camera_id)
        if not self.cap.isOpened():
            raise RuntimeError(f"Não foi possível abrir a câmera {self.camera_id}")
        
        # Configurações da câmera
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        logger.info(f"Câmera {self.camera_id} iniciada com sucesso")
    
    async def recv(self):
        """Recebe o próximo frame"""
        if self.cap is None:
            raise RuntimeError("Câmera não inicializada")
        
        ret, frame = self.cap.read()
        if not ret:
            logger.error("Falha ao capturar frame da câmera")
            raise RuntimeError("Falha na captura da câmera")
        
        # Converte BGR para RGB (OpenCV usa BGR, WebRTC usa RGB)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Cria um frame para aiortc
        from aiortc import VideoFrame
        av_frame = VideoFrame.from_ndarray(frame_rgb, format="rgb24")
        av_frame.pts = self.next_timestamp()
        av_frame.time_base = 1/30  # 30 FPS
        
        return av_frame
    
    def stop(self):
        """Para a captura da câmera"""
        if self.cap:
            self.cap.release()
            self.cap = None
            logger.info("Câmera liberada")

class WebRTCClient:
    def __init__(self, client_id: str, signaling_server_url: str):
        self.client_id = client_id
        self.signaling_server_url = signaling_server_url
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.peer_connection: Optional[RTCPeerConnection] = None
        self.video_track: Optional[CameraVideoStreamTrack] = None
        self.data_channel = None
        self.ice_servers = []
        self.connected_peer = None
        self.running = False
        
        # Display window
        self.display_thread = None
        self.remote_frames = []
        self.remote_frame_lock = threading.Lock()
    
    async def connect_signaling(self):
        """Conecta ao servidor de sinalização"""
        try:
            self.websocket = await websockets.connect(self.signaling_server_url)
            logger.info(f"Conectado ao servidor de sinalização: {self.signaling_server_url}")
            
            # Registra o cliente
            await self.send_signaling_message({
                "type": "register",
                "client_id": self.client_id
            })
            
            return True
        except Exception as e:
            logger.error(f"Erro ao conectar com servidor de sinalização: {e}")
            return False
    
    async def send_signaling_message(self, message: dict):
        """Envia mensagem via WebSocket"""
        if self.websocket:
            try:
                await self.websocket.send(json.dumps(message))
            except Exception as e:
                logger.error(f"Erro ao enviar mensagem: {e}")
    
    async def handle_signaling_messages(self):
        """Processa mensagens do servidor de sinalização"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                await self.process_signaling_message(data)
        except websockets.exceptions.ConnectionClosed:
            logger.info("Conexão com servidor de sinalização encerrada")
        except Exception as e:
            logger.error(f"Erro ao processar mensagens: {e}")
    
    async def process_signaling_message(self, data: dict):
        """Processa mensagem de sinalização recebida"""
        msg_type = data.get("type")
        
        if msg_type == "ice_servers":
            self.ice_servers = data.get("ice_servers", [])
            logger.info(f"Recebida configuração ICE: {self.ice_servers}")
        
        elif msg_type == "existing_peers":
            peers = data.get("peers", [])
            logger.info(f"Peers existentes na sala: {peers}")
            # Inicia conexão com o primeiro peer (assumindo comunicação 1:1)
            if peers:
                await self.initiate_connection(peers[0])
        
        elif msg_type == "peer_joined":
            peer_id = data.get("peer_id")
            logger.info(f"Novo peer conectado: {peer_id}")
        
        elif msg_type == "offer":
            await self.handle_offer(data)
        
        elif msg_type == "answer":
            await self.handle_answer(data)
        
        elif msg_type == "ice_candidate":
            await self.handle_ice_candidate(data)
    
    async def create_peer_connection(self):
        """Cria uma nova conexão WebRTC"""
        config = RTCPeerConnection()
        if self.ice_servers:
            from aiortc import RTCConfiguration, RTCIceServer
            ice_servers = []
            for server in self.ice_servers:
                if "username" in server:
                    ice_servers.append(RTCIceServer(
                        urls=server["urls"],
                        username=server["username"],
                        credential=server["credential"]
                    ))
                else:
                    ice_servers.append(RTCIceServer(urls=server["urls"]))
            config = RTCPeerConnection(RTCConfiguration(iceServers=ice_servers))
        
        self.peer_connection = config
        
        # Adiciona track de vídeo
        self.video_track = CameraVideoStreamTrack()
        self.peer_connection.addTrack(self.video_track)
        
        # Cria canal de dados
        self.data_channel = self.peer_connection.createDataChannel("messages")
        self.data_channel.on("open", self.on_data_channel_open)
        self.data_channel.on("message", self.on_data_channel_message)
        
        # Event handlers
        @self.peer_connection.on("connectionstatechange")
        async def on_connectionstatechange():
            logger.info(f"Estado da conexão: {self.peer_connection.connectionState}")
        
        @self.peer_connection.on("icecandidate")
        async def on_icecandidate(candidate):
            if candidate:
                await self.send_signaling_message({
                    "type": "ice_candidate",
                    "client_id": self.client_id,
                    "to": self.connected_peer,
                    "candidate": {
                        "candidate": candidate.candidate,
                        "sdpMLineIndex": candidate.sdpMLineIndex,
                        "sdpMid": candidate.sdpMid,
                    }
                })
        
        @self.peer_connection.on("track")
        def on_track(track):
            logger.info(f"Track recebido: {track.kind}")
            if track.kind == "video":
                asyncio.create_task(self.receive_video_frames(track))
        
        @self.peer_connection.on("datachannel")
        def on_datachannel(channel):
            logger.info(f"Canal de dados recebido: {channel.label}")
            channel.on("message", self.on_data_channel_message)
    
    def on_data_channel_open(self):
        """Callback quando canal de dados é aberto"""
        logger.info("Canal de dados aberto")
        # Envia mensagem de teste
        if self.data_channel:
            self.data_channel.send("Olá do cliente Python!")
    
    def on_data_channel_message(self, message):
        """Callback para mensagens do canal de dados"""
        logger.info(f"Mensagem recebida: {message}")
    
    async def receive_video_frames(self, track):
        """Recebe frames de vídeo do peer remoto"""
        while True:
            try:
                frame = await track.recv()
                # Converte frame para numpy array para exibição
                img = frame.to_ndarray(format="rgb24")
                img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
                
                with self.remote_frame_lock:
                    self.remote_frames = [img_bgr]
                
            except Exception as e:
                logger.error(f"Erro ao receber frame: {e}")
                break
    
    def start_display_window(self):
        """Inicia thread para exibir vídeo"""
        def display_loop():
            while self.running:
                # Exibe vídeo local
                if self.video_track and self.video_track.cap:
                    ret, local_frame = self.video_track.cap.read()
                    if ret:
                        cv2.imshow("Local Video", local_frame)
                
                # Exibe vídeo remoto
                with self.remote_frame_lock:
                    if self.remote_frames:
                        cv2.imshow("Remote Video", self.remote_frames[0])
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                    
                time.sleep(0.033)  # ~30 FPS
            
            cv2.destroyAllWindows()
        
        self.display_thread = threading.Thread(target=display_loop)
        self.display_thread.daemon = True
        self.display_thread.start()
    
    async def initiate_connection(self, peer_id: str):
        """Inicia conexão com um peer"""
        self.connected_peer = peer_id
        await self.create_peer_connection()
        
        # Cria offer
        offer = await self.peer_connection.createOffer()
        await self.peer_connection.setLocalDescription(offer)
        
        await self.send_signaling_message({
            "type": "offer",
            "client_id": self.client_id,
            "to": peer_id,
            "offer": {
                "type": offer.type,
                "sdp": offer.sdp
            }
        })
        
        logger.info(f"Offer enviado para {peer_id}")
    
    async def handle_offer(self, data):
        """Processa offer recebido"""
        peer_id = data.get("from")
        offer_data = data.get("offer")
        
        self.connected_peer = peer_id
        await self.create_peer_connection()
        
        # Define descrição remota
        offer = RTCSessionDescription(sdp=offer_data["sdp"], type=offer_data["type"])
        await self.peer_connection.setRemoteDescription(offer)
        
        # Cria answer
        answer = await self.peer_connection.createAnswer()
        await self.peer_connection.setLocalDescription(answer)
        
        await self.send_signaling_message({
            "type": "answer",
            "client_id": self.client_id,
            "to": peer_id,
            "answer": {
                "type": answer.type,
                "sdp": answer.sdp
            }
        })
        
        logger.info(f"Answer enviado para {peer_id}")
    
    async def handle_answer(self, data):
        """Processa answer recebido"""
        answer_data = data.get("answer")
        answer = RTCSessionDescription(sdp=answer_data["sdp"], type=answer_data["type"])
        await self.peer_connection.setRemoteDescription(answer)
        logger.info("Answer processado")
    
    async def handle_ice_candidate(self, data):
        """Processa ICE candidate recebido"""
        candidate_data = data.get("candidate")
        candidate = RTCIceCandidate(
            candidate=candidate_data["candidate"],
            sdpMLineIndex=candidate_data["sdpMLineIndex"],
            sdpMid=candidate_data["sdpMid"]
        )
        await self.peer_connection.addIceCandidate(candidate)
    
    async def join_room(self, room_id: str):
        """Entra em uma sala"""
        await self.send_signaling_message({
            "type": "join_room",
            "client_id": self.client_id,
            "room_id": room_id
        })
        logger.info(f"Entrando na sala: {room_id}")
    
    async def send_message(self, message: str):
        """Envia mensagem via canal de dados"""
        if self.data_channel and self.data_channel.readyState == "open":
            self.data_channel.send(message)
            logger.info(f"Mensagem enviada: {message}")
    
    async def run(self, room_id: str = "default"):
        """Executa o cliente"""
        self.running = True
        
        # Conecta ao servidor de sinalização
        if not await self.connect_signaling():
            return
        
        # Inicia janela de exibição
        self.start_display_window()
        
        # Entra na sala
        await self.join_room(room_id)
        
        # Processa mensagens de sinalização
        await self.handle_signaling_messages()
    
    def stop(self):
        """Para o cliente"""
        self.running = False
        
        if self.video_track:
            self.video_track.stop()
        
        if self.peer_connection:
            asyncio.create_task(self.peer_connection.close())

async def main():
    """Função principal"""
    client_id = "python_client"
    signaling_url = "ws://localhost:8765"
    
    client = WebRTCClient(client_id, signaling_url)
    
    # Handler para encerramento gracioso
    def signal_handler(signum, frame):
        logger.info("Encerrando cliente...")
        client.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        await client.run()
    except Exception as e:
        logger.error(f"Erro na execução: {e}")
    finally:
        client.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Cliente encerrado pelo usuário")
