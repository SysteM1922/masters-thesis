#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <sys/time.h>
#include <time.h>
#include <errno.h>

#define PORT 8888
#define BUFFER_SIZE 1024

// Tipos de mensagens PTP
typedef enum {
    PTP_SYNC_REQUEST = 1,
    PTP_SYNC_RESPONSE = 2,
    PTP_DELAY_REQUEST = 3,
    PTP_DELAY_RESPONSE = 4,
    PTP_BUSY = 5
} ptp_msg_type_t;

// Estrutura da mensagem PTP
typedef struct {
    ptp_msg_type_t type;
    struct timeval timestamp;
    int client_id;
} ptp_message_t;

// Função para obter timestamp atual
struct timeval get_current_time() {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return tv;
}

// Função para imprimir timestamp
void print_timestamp(struct timeval tv, const char* label) {
    printf("%s: %ld.%06ld\n", label, tv.tv_sec, tv.tv_usec);
}

int main() {
    int sockfd;
    struct sockaddr_in server_addr, client_addr;
    socklen_t client_len = sizeof(client_addr);
    ptp_message_t msg, response;
    int serving_client = 0; // 0 = livre, 1 = ocupado
    int current_client_id = -1;
    struct sockaddr_in current_client_addr;
    
    // Criar socket UDP
    if ((sockfd = socket(AF_INET, SOCK_DGRAM, 0)) < 0) {
        perror("Erro ao criar socket");
        exit(EXIT_FAILURE);
    }
    
    // Configurar endereço do servidor
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;
    server_addr.sin_port = htons(PORT);
    
    // Bind do socket
    if (bind(sockfd, (const struct sockaddr*)&server_addr, sizeof(server_addr)) < 0) {
        perror("Erro no bind");
        close(sockfd);
        exit(EXIT_FAILURE);
    }
    
    printf("Servidor PTP iniciado na porta %d\n", PORT);
    printf("Aguardando clientes...\n\n");
    
    while (1) {
        // Receber mensagem do cliente
        ssize_t n = recvfrom(sockfd, &msg, sizeof(msg), 0, 
                            (struct sockaddr*)&client_addr, &client_len);
        
        if (n < 0) {
            perror("Erro ao receber mensagem");
            continue;
        }
        
        printf("Mensagem recebida do cliente %s:%d (ID: %d, Tipo: %d)\n", 
               inet_ntoa(client_addr.sin_addr), ntohs(client_addr.sin_port), 
               msg.client_id, msg.type);
        
        // Verificar se o servidor está ocupado com outro cliente
        if (serving_client && msg.client_id != current_client_id) {
            printf("Servidor ocupado - rejeitando cliente %d\n", msg.client_id);
            response.type = PTP_BUSY;
            response.timestamp = get_current_time();
            response.client_id = msg.client_id;
            
            sendto(sockfd, &response, sizeof(response), 0, 
                   (const struct sockaddr*)&client_addr, client_len);
            continue;
        }
        
        switch (msg.type) {
            case PTP_SYNC_REQUEST:
                printf("Processando SYNC_REQUEST do cliente %d\n", msg.client_id);
                
                // Marcar servidor como ocupado
                serving_client = 1;
                current_client_id = msg.client_id;
                current_client_addr = client_addr;
                
                // Responder com SYNC_RESPONSE
                response.type = PTP_SYNC_RESPONSE;
                response.timestamp = get_current_time();
                response.client_id = msg.client_id;
                
                print_timestamp(response.timestamp, "T2 (Server Sync Response)");
                
                sendto(sockfd, &response, sizeof(response), 0, 
                       (const struct sockaddr*)&client_addr, client_len);
                break;
                
            case PTP_DELAY_REQUEST:
                printf("Processando DELAY_REQUEST do cliente %d\n", msg.client_id);
                
                // Responder com DELAY_RESPONSE
                response.type = PTP_DELAY_RESPONSE;
                response.timestamp = get_current_time();
                response.client_id = msg.client_id;
                
                print_timestamp(response.timestamp, "T4 (Server Delay Response)");
                
                sendto(sockfd, &response, sizeof(response), 0, 
                       (const struct sockaddr*)&client_addr, client_len);
                
                // Liberar servidor após completar a sincronização
                serving_client = 0;
                current_client_id = -1;
                printf("Sincronização com cliente %d concluída\n\n", msg.client_id);
                break;
                
            default:
                printf("Tipo de mensagem desconhecido: %d\n", msg.type);
                break;
        }
    }
    
    close(sockfd);
    return 0;
}