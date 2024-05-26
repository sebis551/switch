#!/usr/bin/python3
import sys
import struct
import wrapper
import threading
import time
from wrapper import recv_from_any_link, send_to_link, get_switch_mac, get_interface_name




def parse_ethernet_header(data):
    # Unpack the header fields from the byte array
    #dest_mac, src_mac, ethertype = struct.unpack('!6s6sH', data[:14])
    dest_mac = data[0:6]
    src_mac = data[6:12]
    
    # Extract ethertype. Under 802.1Q, this may be the bytes from the VLAN TAG
    ether_type = (data[12] << 8) + data[13]

    vlan_id = -1
    # Check for VLAN tag (0x8100 in network byte order is b'\x81\x00')
    if ether_type == 0x8200:
        vlan_tci = int.from_bytes(data[14:16], byteorder='big')
        vlan_id = vlan_tci & 0x0FFF  # extract the 12-bit VLAN ID
        ether_type = (data[16] << 8) + data[17]

    return dest_mac, src_mac, ether_type, vlan_id

def create_vlan_tag(vlan_id):
    # 0x8100 for the Ethertype for 802.1Q
    # vlan_id & 0x0FFF ensures that only the last 12 bits are used
    return struct.pack('!H', 0x8200) + struct.pack('!H', vlan_id & 0x0FFF)

def send_bdpu_every_sec():
    fisieru = "configs/switch" + str(sys.argv[1]) + ".cfg"
    fd = open(fisieru, 'r')
    switch_priority = int(fd.readline())
    while True:
        # TODO Send BDPU every second if necessary
        data = []
        
        finalmac = b'\x01\x80\xC2\x00\x00\x00'
        data[0:6] = finalmac
        data[6:12] = get_switch_mac()
        if(root_bridge_ID == own_bridge_ID):
            data[12:16] = own_bridge_ID.to_bytes(4, 'big')
            data[16:20] = own_bridge_ID.to_bytes(4, 'big')
            data[20:24] = root_path_cost.to_bytes(4, 'big')
            buf = b''
            buf += b'\x01\x80\xC2\x00\x00\x00'
            buf += get_switch_mac()
            buf += own_bridge_ID.to_bytes(4, 'big')
            buf += own_bridge_ID.to_bytes(4, 'big')
            buf += root_path_cost.to_bytes(4, 'big')
            for i in interfaces2:
                if get_interface_name(i) in vlan_table:
                    if vlan_table[get_interface_name(i)] == "T":
                        
                        send_to_link(i, buf, 24)

        time.sleep(1)

def main():
    # init returns the max interface number. Our interfaces
    # are 0, 1, 2, ..., init_ret value + 1
    switch_id = sys.argv[1]

    num_interfaces = wrapper.init(sys.argv[2:])
    
    interfaces = range(0, num_interfaces)

    global vlan_table
    global interfaces2
    interfaces2 = interfaces
    mac_table = {}
    vlan_table = {}
    blocked_table = {}
    

    fisieru = "configs/switch" + str(switch_id) + ".cfg"
    
    with open(fisieru, 'r') as file:
        switch_priority = int(file.readline())
        for line in file:
            words = line.split()
            for word1, word2 in zip(words[:-1], words[1:]):
                vlan_table[word1] = word2
                
    
                
            
        

    
   

    for i in interfaces:
        if vlan_table[get_interface_name(i)] == "T":
            root_port = vlan_table[get_interface_name(i)]
            blocked_table[get_interface_name(i)] = vlan_table.pop(get_interface_name(i))
            

    global own_bridge_ID
    global root_bridge_ID
    global root_path_cost
    own_bridge_ID =  switch_priority
    root_bridge_ID = own_bridge_ID
    root_path_cost = 0

    if own_bridge_ID == root_bridge_ID:
        for i in interfaces:
            if get_interface_name(i) in blocked_table:
                vlan_table[get_interface_name(i)] = blocked_table.pop(get_interface_name(i))

    
    # Create and start a new thread that deals with sending BDPU
    t = threading.Thread(target=send_bdpu_every_sec)
    t.start()


        

    while True:
        # Note that data is of type bytes([...]).
        # b1 = bytes([72, 101, 108, 108, 111])  # "Hello"
        # b2 = bytes([32, 87, 111, 114, 108, 100])  # " World"
        # b3 = b1[0:2] + b[3:4].
        interface, data, length = recv_from_any_link()
        

        dest_mac, src_mac, ethertype, vlan_id = parse_ethernet_header(data)
        

        if dest_mac == b'\x01\x80\xC2\x00\x00\x00':
            
            bpdu_sender = int.from_bytes(data[16:20], 'big')
            bpdu_root = int.from_bytes(data[12:16], 'big')
            bpdu_cost = int.from_bytes(data[20:24], 'big')
            
            last_root = root_bridge_ID
            if bpdu_root < root_bridge_ID:
                root_bridge_ID = bpdu_root
                root_path_cost = bpdu_cost + 10
                root_port = get_interface_name(interface)

                if last_root == own_bridge_ID:
                    for i in interfaces:
                        if vlan_table[get_interface_name(i)] == "T" and get_interface_name(i) != get_interface_name(interface):
                            blocked_table[get_interface_name(i)] = vlan_table.pop(get_interface_name(i))
                if root_port in blocked_table:
                    vlan_table[root_port] = blocked_table.pop(root_port)
                
                buf = b''
                buf += b'\x01\x80\xC2\x00\x00\x00'
                buf += get_switch_mac()
                buf += root_bridge_ID.to_bytes(4, 'big')
                buf += own_bridge_ID.to_bytes(4, 'big')
                buf += root_path_cost.to_bytes(4, 'big')
                for i in interfaces2:
                    if get_interface_name(i) in vlan_table and get_interface_name(i) != get_interface_name(interface):
                        if vlan_table[get_interface_name(i)] == "T":
                            
                            send_to_link(i, buf, 24)
                    if get_interface_name(i) in blocked_table and get_interface_name(i) != get_interface_name(interface):
                        if blocked_table[get_interface_name(i)] == "T":
                            
                            send_to_link(i, buf, 24)
            else:
                if bpdu_root == root_bridge_ID:
                    if get_interface_name(interface) == root_port and bpdu_cost + 10 < root_path_cost:
                        root_path_cost = bpdu_cost + 10
                    else:
                        if get_interface_name(interface) != root_port:
                            if bpdu_cost > root_path_cost:
                                if get_interface_name(interface) in blocked_table:
                                    vlan_table.pop[get_interface_name(interface)] = blocked_table.pop(get_interface_name(interface))
                if bpdu_sender == own_bridge_ID:
                    if get_interface_name(interface) in vlan_table:
                        blocked_table[get_interface_name(i)] = vlan_table.pop(get_interface_name(i))
                else: 
                    continue
            if own_bridge_ID == root_bridge_ID:
                for i in blocked_table:
                    vlan_table[i] = blocked_table.pop(i)            

                
            continue
        # Print the MAC src and MAC dst in human readable format
        dest_mac = ':'.join(f'{b:02x}' for b in dest_mac)
        src_mac = ':'.join(f'{b:02x}' for b in src_mac)

        # Note. Adding a VLAN tag can be as easy as
        # tagged_frame = data[0:12] + create_vlan_tag(10) + data[12:]


        
        
            
                      
        # TODO: Implement forwarding with learning
       
        mac_table[src_mac] = interface
        if vlan_table[get_interface_name(interface)] == "T":
            
            if data[0] & 1 == 0:
                if dest_mac in mac_table:
                   
                   
                    
                    if vlan_table[get_interface_name(mac_table[dest_mac])] == "T":
                        send_to_link(mac_table[dest_mac], data, length)
                    else:    
                        

                        if str(vlan_id) == vlan_table[get_interface_name(mac_table[dest_mac])]:
                            notagged_frame = data[0:12] + data[16:]
                            send_to_link(mac_table[dest_mac], notagged_frame, length-4)
                else:   
                    
                    for i in interfaces:
                        if i != mac_table[src_mac] and get_interface_name(i) in vlan_table:

                            
                            if(vlan_table[get_interface_name(i)] == "T"):
                                send_to_link(i, data, length)
                               
                            else:
                                

                               
                                if vlan_table[get_interface_name(i)] == str(vlan_id):
                                    notagged_frame = data[0:12] + data[16:]
                                    send_to_link(i, notagged_frame, length-4)

            else:
                
                for i in interfaces:
                   
                    if i != mac_table[src_mac] and get_interface_name(i) in vlan_table:
                        if(vlan_table[get_interface_name(i)] == "T"):
                                send_to_link(i, data, length)
                        else:
                            
                            if vlan_table[get_interface_name(i)] == str(vlan_id) :
                                notagged_frame = data[0:12] + data[16:]
                                send_to_link(i, notagged_frame, length-4)
        else:
            
            
            if data[0] & 1 == 0:
                if dest_mac in mac_table:
                    if vlan_table[get_interface_name(mac_table[dest_mac])] == "T":
                        

                        tagged_frame = data[0:12] + create_vlan_tag(int(vlan_table[get_interface_name(interface)])) + data[12:]
                        send_to_link(mac_table[dest_mac], tagged_frame, length + 4)
                    else:    
                        if(vlan_table[get_interface_name(mac_table[dest_mac])] == vlan_table[get_interface_name(interface)]):
                            send_to_link(mac_table[dest_mac], data, length)
                else:
                    for i in interfaces:
                        if i != mac_table[src_mac] and get_interface_name(i) in vlan_table:
                            if(vlan_table[get_interface_name(i)] == "T"):
                                
                                tagged_frame = data[0:12] + create_vlan_tag(int(vlan_table[get_interface_name(interface)])) + data[12:]
                                send_to_link(i, tagged_frame, length + 4)
                            else:
                             
                                if(vlan_table[get_interface_name(i)] == vlan_table[get_interface_name(interface)]):
                                    send_to_link(i, data, length)

            else:
                for i in interfaces:
                    if i != mac_table[src_mac] and get_interface_name(i) in vlan_table:
                        if(vlan_table[get_interface_name(i)] == "T"):
                            tagged_frame = data[0:12] + create_vlan_tag(int(vlan_table[get_interface_name(interface)])) + data[12:]
                            send_to_link(i, tagged_frame, length + 4)
                        else:
                            if(vlan_table[get_interface_name(i)] == vlan_table[get_interface_name(interface)]):
                                    send_to_link(i, data, length)


        

        # TODO: Implement VLAN support


        # TODO: Implement STP support

        # data is of type bytes.
        # send_to_link(i, data, length)

if __name__ == "__main__":
    main()
