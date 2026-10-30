/* Exact squared Euclidean distance for |x|,|y| <= 1,000,000,000.
 * C11; independently authored. Returns any closest pair of distinct indices.
 * The input is not modified. Return 1 on success; 0 on invalid input/allocation.
 */
#include <stdint.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>

typedef struct { int32_t x, y; } Point;
typedef struct { Point p; size_t id; } Item;
typedef struct { size_t first, second; uint64_t distance2; } Closest;

static int less(Item a, Item b, int by_y) {
    int32_t u = by_y ? a.p.y : a.p.x, v = by_y ? b.p.y : b.p.x;
    if (u != v) return u < v;
    u = by_y ? a.p.x : a.p.y; v = by_y ? b.p.x : b.p.y;
    return u != v ? u < v : a.id < b.id;
}
static uint64_t square(int64_t value) { return (uint64_t)(value * value); }
static void consider(Item a, Item b, Closest *best) {
    uint64_t d = square((int64_t)a.p.x-b.p.x) + square((int64_t)a.p.y-b.p.y);
    if (d < best->distance2) {
        best->first = a.id; best->second = b.id; best->distance2 = d;
    }
}
static void merge(Item *a, Item *tmp, size_t lo, size_t mid, size_t hi, int by_y) {
    size_t i=lo, j=mid, k=lo;
    while (i<mid && j<hi) tmp[k++] = less(a[j],a[i],by_y) ? a[j++] : a[i++];
    while (i<mid) tmp[k++]=a[i++];
    while (j<hi) tmp[k++]=a[j++];
    memcpy(a+lo,tmp+lo,(hi-lo)*sizeof(*a));
}
static void sort_x(Item *a, Item *tmp, size_t lo, size_t hi) {
    if (hi-lo<2) return;
    size_t mid=lo+(hi-lo)/2;
    sort_x(a,tmp,lo,mid); sort_x(a,tmp,mid,hi); merge(a,tmp,lo,mid,hi,0);
}
/* Entry: x order; exit: y order. All pair candidates improve a global bound. */
static void solve(Item *a, Item *tmp, size_t lo, size_t hi, Closest *best) {
    if (hi-lo<=3) {
        for (size_t i=lo;i<hi;i++) for (size_t j=i+1;j<hi;j++) consider(a[i],a[j],best);
        for (size_t i=lo+1;i<hi;i++) {
            Item v=a[i]; size_t j=i;
            while (j>lo && less(v,a[j-1],1)) { a[j]=a[j-1]; --j; }
            a[j]=v;
        }
        return;
    }
    size_t mid=lo+(hi-lo)/2; int32_t split=a[mid].p.x;
    solve(a,tmp,lo,mid,best); solve(a,tmp,mid,hi,best);
    merge(a,tmp,lo,mid,hi,1);
    if (best->distance2==0) return;
    size_t count=0;
    for (size_t i=lo;i<hi;i++)
        if (square((int64_t)a[i].p.x-split)<best->distance2) tmp[lo+count++]=a[i];
    for (size_t i=0;i<count;i++) for (size_t j=i+1;j<count;j++) {
        if (square((int64_t)tmp[lo+j].p.y-tmp[lo+i].p.y)>=best->distance2) break;
        consider(tmp[lo+i],tmp[lo+j],best);
    }
}
int closest_pair(const Point *points, size_t n, Closest *out) {
    if (!points || !out || n<2 || n>SIZE_MAX/sizeof(Item)) return 0;
    for (size_t i=0;i<n;i++)
        if (points[i].x < -1000000000 || points[i].x > 1000000000 ||
            points[i].y < -1000000000 || points[i].y > 1000000000) return 0;
    Item *a=malloc(n*sizeof(*a)), *tmp=malloc(n*sizeof(*tmp));
    if (!a || !tmp) { free(a); free(tmp); return 0; }
    for (size_t i=0;i<n;i++) { a[i].p=points[i]; a[i].id=i; }
    Closest best={0,1,UINT64_MAX};
    sort_x(a,tmp,0,n); solve(a,tmp,0,n,&best);
    *out=best; free(tmp); free(a); return 1;
}
