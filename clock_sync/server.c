#ifdef _WIN32
#include <winsock.h>
#else
#include <sys/socket.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <time.h>
#endif

#include <stdio.h>
#include <stdlib.h>

#define PORT 10000          // Port number for the server
#define BUFFER_SIZE 32      // Size of the buffer for sending and receiving data

double get_current_time() {
#ifdef _WIN32
    FILETIME ft;                            // File time structure
    GetSystemTimePreciseAsFileTime(&ft);    // Get the current system time in precise file time format
    ULARGE_INTEGER uli;               // Union to hold the file time as a large integer
    uli.LowPart = ft.dwLowDateTime;             
    uli.HighPart = ft.dwHighDateTime;
    return (double)uli.QuadPart / 10000.0;  // Convert to milliseconds
#else
    struct timespec ts;           // Timespec structure for POSIX time representation
    clockgettime(CLOCK_REALTIME, &ts);  // Get the current time in seconds and nanoseconds
    return (ts.tv_sec * 1000.0) + (ts.tv_nsec / 1000000.0);  // Convert to milliseconds
#endif
}

int main() {
#ifdef _WIN32
    WSADATA wsa;        // Winsock data structure
    if (WSAStartup(MAKEWORD(2, 2), &wsa) != 0) {  // Initialize Winsock
        printf("Failed to initialize Winsock. Error Code: %d\n", WSAGetLastError());
        return 1;
    }
#endif

    int sock;   // Socket descriptor
    struct sockaddr_in server_addr, client_addr;  // Server and client address structures
    char buffer[BUFFER_SIZE];  // Buffer for sending and receiving data

    sock = socket(AF_INET, SOCK_DGRAM, 0);  // Create a UDP socket
    if (sock < 0) {
        perror("Socket creation failed");
        return 1;
    }

    memset(&server_addr, 0, sizeof(server_addr));  // Clear the server address structure
    server_addr.sin_family = AF_INET;  // Set address family to IPv4
    server_addr.sin_port = htons(PORT);  // Set port number, converting to network byte order
    server_addr.sin_addr.s_addr = htonl(INADDR_ANY);  // Bind to any available address

    if (bind(sock, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {  // Bind the socket to the address
        perror("Bind failed");
        return 1;
    }

    printf("Server is running on port %d\n", PORT);

    while(1) {

    }

#ifdef _WIN32
    closesocket(sock);  // Close the socket
    WSACleanup();  // Clean up Winsock resources
#else
    close(sock);  // Close the socket
#endif

    return 0;  // Exit the program
}