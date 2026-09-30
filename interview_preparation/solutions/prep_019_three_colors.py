"""In-place three-way partition: blue, green, red. Colors are B/G/R."""
def sort_three_colors(items,key=lambda item:item):
    low=mid=0
    high=len(items)-1
    while mid<=high:
        color=key(items[mid])
        if color=='B':
            items[low],items[mid]=items[mid],items[low]
            low+=1
            mid+=1
        elif color=='G':
            mid+=1
        elif color=='R':
            items[mid],items[high]=items[high],items[mid]
            high-=1
            # The replacement at mid was unclassified; do not advance mid.
        else:
            raise ValueError('Expected only B, G or R')
    return items
