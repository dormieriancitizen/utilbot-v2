from num2words import num2words

def node(base,nodes,num):
    if num in nodes:
        # Either already checked, or infinite loop
        return False
    
    string = base + num2words(num)

    length = len(string)

    if length == num:
        return num

    nodes[num] = length

    subnode = node(base,nodes,length)
    if subnode:
        return subnode
    

def gen_recursive_string(text):
    nodes = {}
    base = text.replace("!(count)","")

    guess = len(base)

    i = 0
    sentence = ""
    while True:
        count = node(base,nodes,guess+i)
        if count:
            sentence = text.replace("!(count)",num2words(count))
            print(f"Matched in {i} paths")
            if i == 0:
                print("I guess all roads really do lead to rome")
            break
        i+=1

        if i > len(text*100):
            sentence = f"Could not find match in {i} attempts"
            break

    return sentence