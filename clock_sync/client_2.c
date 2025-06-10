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

#define SERVER_PORT 8888
#define BUFFER_SIZE 1024
#define MAX_RETRIES 5
#define RETRY_DELAY 2 // segundos

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

// Função para calcular diferença entre timestamps em microssegundos
long long time_diff_us(struct timeval t1, struct timeval t2) {
    return ((long long)(t2.tv_sec - t1.tv_sec) * 1000000LL) + (t2.tv_usec - t1.tv_usec);
}

// Função para imprimir timestamp
void print_timestamp(struct timeval tv, const char* label) {
    printf("%s: %ld.%06ld\n", label, tv.tv_sec, tv.tv_usec);
}

// Função para escrever resultado no arquivo
void write_result_to_file(long long offset_us, int client_id) {
    FILE *file = fopen("ptp_result.txt", "w");
    if (file == NULL) {
        perror("Erro ao abrir arquivo para escrita");
        return;
    }
    
    fprintf(file, "Cliente ID: %d\n", client_id);
    fprintf(file, "Diferença de relógio: %lld microssegundos\n", offset_us);
    fprintf(file, "Diferença de relógio: %.6f segundos\n", offset_us / 1000000.0);
    
    if (offset_us > 0) {
        fprintf(file, "Relógio do cliente está %lld μs atrasado em relação ao servidor\n", offset_us);
    } else if (offset_us < 0) {
        fprintf(file, "Relógio do cliente está %lld μs adiantado em relação ao servidor\n", -offset_us);
    } else {
        fprintf(file, "Relógios estão sincronizados\n");
    }
    
    fclose(file);
    printf("Resultado escrito no arquivo 'ptp_result.txt'\n");
}

int main(int argc, char *argv[]) {
    if (argc != 2) {
        printf("Uso: %s <IP_do_servidor>\n", argv[0]);
        exit(EXIT_FAILURE);
    }
    
    int sockfd;
    struct sockaddr_in server_addr;
    ptp_message_t msg, response;
    socklen_t server_len = sizeof(server_addr);
    int client_id = getpid(); // Usar PID como ID único do cliente
    
    // Timestamps para PTP
    struct timeval t1, t2, t3, t4;
    
    // Criar socket UDP
    if ((sockfd = socket(AF_INET, SOCK_DGRAM, 0)) < 0) {
        perror("Erro ao criar socket");
        exit(EXIT_FAILURE);
    }
    
    // Configurar timeout para receive
    struct timeval timeout;
    timeout.tv_sec = 5;
    timeout.tv_usec = 0;
    if (setsockopt(sockfd, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout)) < 0) {
        perror("Erro ao configurar timeout");
        close(sockfd);
        exit(EXIT_FAILURE);
    }
    
    // Configurar endereço do servidor
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(SERVER_PORT);
    
    if (inet_pton(AF_INET, argv[1], &server_addr.sin_addr) <= 0) {
        printf("Endereço IP inválido: %s\n", argv[1]);
        close(sockfd);
        exit(EXIT_FAILURE);
    }
    
    printf("Cliente PTP iniciado (ID: %d)\n", client_id);
    printf("Conectando ao servidor %s:%d\n\n", argv[1], SERVER_PORT);
    
    int retries = 0;
    int sync_completed = 0;
    
    while (!sync_completed && retries < MAX_RETRIES) {
        printf("=== Tentativa de sincronização %d ===\n", retries + 1);
        
        // Fase 1: SYNC_REQUEST
        printf("Enviando SYNC_REQUEST...\n");
        msg.type = PTP_SYNC_REQUEST;
        t1 = get_current_time(); // T1: timestamp do cliente antes do envio
        msg.timestamp = t1;
        msg.client_id = client_id;
        
        print_timestamp(t1, "T1 (Client Sync Request)");
        
        if (sendto(sockfd, &msg, sizeof(msg), 0, 
                   (const struct sockaddr*)&server_addr, server_len) < 0) {
            perror("Erro ao enviar SYNC_REQUEST");
            retries++;
            sleep(RETRY_DELAY);
            continue;
        }
        
        // Receber SYNC_RESPONSE
        ssize_t n = recvfrom(sockfd, &response, sizeof(response), 0, 
                            (struct sockaddr*)&server_addr, &server_len);
        
        if (n < 0) {
            if (errno == EAGAIN || errno == EWOULDBLOCK) {
                printf("Timeout ao aguardar SYNC_RESPONSE\n");
            } else {
                perror("Erro ao receber SYNC_RESPONSE");
            }
            retries++;
            sleep(RETRY_DELAY);
            continue;
        }
        
        if (response.type == PTP_BUSY) {
            printf("Servidor ocupado. Tentando novamente em %d segundos...\n", RETRY_DELAY);
            retries++;
            sleep(RETRY_DELAY);
            continue;
        }
        
        if (response.type != PTP_SYNC_RESPONSE) {
            printf("Resposta inesperada: %d\n", response.type);
            retries++;
            sleep(RETRY_DELAY);
            continue;
        }
        
        t2 = response.timestamp; // T2: timestamp do servidor ao receber SYNC_REQUEST
        print_timestamp(t2, "T2 (Server Sync Response)");
        
        // Fase 2: DELAY_REQUEST
        printf("Enviando DELAY_REQUEST...\n");
        msg.type = PTP_DELAY_REQUEST;
        t3 = get_current_time(); // T3: timestamp do cliente antes do DELAY_REQUEST
        msg.timestamp = t3;
        msg.client_id = client_id;
        
        print_timestamp(t3, "T3 (Client Delay Request)");
        
        if (sendto(sockfd, &msg, sizeof(msg), 0, 
                   (const struct sockaddr*)&server_addr, server_len) < 0) {
            perror("Erro ao enviar DELAY_REQUEST");
            retries++;
            sleep(RETRY_DELAY);
            continue;
        }
        
        // Receber DELAY_RESPONSE
        n = recvfrom(sockfd, &response, sizeof(response), 0, 
                     (struct sockaddr*)&server_addr, &server_len);
        
        if (n < 0) {
            if (errno == EAGAIN || errno == EWOULDBLOCK) {
                printf("Timeout ao aguardar DELAY_RESPONSE\n");
            } else {
                perror("Erro ao receber DELAY_RESPONSE");
            }
            retries++;
            sleep(RETRY_DELAY);
            continue;
        }
        
        if (response.type != PTP_DELAY_RESPONSE) {
            printf("Resposta inesperada: %d\n", response.type);
            retries++;
            sleep(RETRY_DELAY);
            continue;
        }
        
        t4 = response.timestamp; // T4: timestamp do servidor ao receber DELAY_REQUEST
        print_timestamp(t4, "T4 (Server Delay Response)");
        
        // Calcular offset do relógio
        // Offset = ((T2 - T1) + (T3 - T4)) / 2
        long long delay_ms = time_diff_us(t1, t2); // T2 - T1
        long long delay_sm = time_diff_us(t4, t3); // T3 - T4
        long long offset_us = (delay_ms + delay_sm) / 2;
        
        printf("\n=== Resultado da Sincronização ===\n");
        printf("Delay Master->Slave: %lld μs\n", delay_ms);
        printf("Delay Slave->Master: %lld μs\n", delay_sm);
        printf("Offset do relógio: %lld μs (%.6f segundos)\n", offset_us, offset_us / 1000000.0);
        
        if (offset_us > 0) {
            printf("Relógio do cliente está %lld μs atrasado em relação ao servidor\n", offset_us);
        } else if (offset_us < 0) {
            printf("Relógio do cliente está %lld μs adiantado em relação ao servidor\n", -offset_us);
        } else {
            printf("Relógios estão sincronizados\n");
        }
        
        // Escrever resultado no arquivo
        write_result_to_file(offset_us, client_id);
        
        sync_completed = 1;
        printf("\nSincronização concluída com sucesso!\n");
    }
    
    if (!sync_completed) {
        printf("Falha na sincronização após %d tentativas\n", MAX_RETRIES);
    }
    
    close(sockfd);
    return sync_completed ? 0 : 1;
}