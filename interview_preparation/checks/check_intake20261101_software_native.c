/* Strict C99 independent public-API tests with allocation failure injection. */
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>

static unsigned long assertions, dictionary_cases, reverse_cases, arena_steps;
#define CHECK(x) do { ++assertions; if (!(x)) { fprintf(stderr,"failed:%d\n",__LINE__); exit(1); } } while (0)
static void *live[128];
static size_t live_count;
static int remaining_allocations = -1;
static void *checked_malloc(size_t size) {
    if (remaining_allocations == 0) return NULL;
    if (remaining_allocations > 0) --remaining_allocations;
    void *pointer = malloc(size);
    CHECK(pointer != NULL);
    for (size_t i=0;i<128;++i) if (!live[i]) {
        live[i]=pointer; ++live_count; return pointer;
    }
    CHECK(false); return NULL;
}
static void checked_free(void *pointer) {
    if (!pointer) return;
    for (size_t i=0;i<128;++i) if (live[i] == pointer) {
        live[i]=NULL; --live_count; free(pointer); return;
    }
    CHECK(false);
}
#define malloc checked_malloc
#define free checked_free
#include "../solutions/prep_237_dictionary.c"
#undef malloc
#undef free
#include "../solutions/prep_238_reverse_linked_list.c"
#include "../solutions/prep_117_int_arena_batch1101.c"

static void check_dictionary(void) {
    remaining_allocations=0; CHECK(dict_create()==NULL); CHECK(live_count==0);
    remaining_allocations=-1;
    Dict *dict=dict_create(); CHECK(dict!=NULL);
    char key[]="key",value[]="old";
    CHECK(dict_put(dict,key,value)==DICT_OK); key[0]='X'; value[0]='X';
    CHECK(strcmp(dict_get(dict,"key"),"old")==0 && dict_get(dict,"Xey")==NULL);
    size_t before=live_count;
    remaining_allocations=0;
    CHECK(dict_put(dict,"key","new")==DICT_OOM);
    CHECK(dict_size(dict)==1 && strcmp(dict_get(dict,"key"),"old")==0 && live_count==before);
    for (int allowed=0;allowed<3;++allowed) {
        remaining_allocations=allowed;
        CHECK(dict_put(dict,"newkey","newvalue")==DICT_OOM);
        CHECK(dict_size(dict)==1 && dict_get(dict,"newkey")==NULL && live_count==before);
    }
    remaining_allocations=-1;
    CHECK(dict_put(dict,"key",dict_get(dict,"key"))==DICT_OK);
    CHECK(strcmp(dict_get(dict,"key"),"old")==0 && live_count==before);
    CHECK(dict_put(dict,"","empty-key")==DICT_OK);
    CHECK(strcmp(dict_get(dict,""),"empty-key")==0);
    CHECK(dict_put(NULL,"x","y")==DICT_INVALID);
    CHECK(dict_put(dict,NULL,"y")==DICT_INVALID);
    CHECK(dict_put(dict,"x",NULL)==DICT_INVALID);
    CHECK(dict_remove(dict,"missing")==DICT_NOT_FOUND);
    dict_destroy(dict); dict_destroy(NULL); CHECK(live_count==0);

    const char *keys[]={"","a","B"}, *values[]={"0","new",""};
    unsigned histories=1;
    for (unsigned length=0;length<=5;++length,histories*=9) {
        for (unsigned encoding=0;encoding<histories;++encoding) {
            bool present[3]={false,false,false}; unsigned expected[3]={0,0,0};
            dict=dict_create(); unsigned digits=encoding;
            for (unsigned step=0;step<length;++step) {
                unsigned op=digits%9; digits/=9; unsigned k=op%3;
                if (op<3) {
                    CHECK(dict_put(dict,keys[k],values[step%3])==DICT_OK);
                    present[k]=true; expected[k]=step%3;
                } else if (op<6) {
                    DictStatus status=dict_remove(dict,keys[k]);
                    CHECK(status==(present[k]?DICT_OK:DICT_NOT_FOUND)); present[k]=false;
                }
                size_t count=0;
                for (unsigned j=0;j<3;++j) {
                    const char *actual=dict_get(dict,keys[j]);
                    CHECK(present[j] ? actual && strcmp(actual,values[expected[j]])==0 : actual==NULL);
                    count+=present[j];
                }
                CHECK(dict_size(dict)==count);
            }
            dict_destroy(dict); CHECK(live_count==0); ++dictionary_cases;
        }
    }
}

static void check_reversal(void) {
    for (size_t length=0;length<=8;++length) {
        for (unsigned pattern=0;pattern<(1u<<length);++pattern) {
            ReverseNode nodes[8];
            for(size_t i=0;i<length;++i) {nodes[i].value=(int)((pattern>>i)&1u); nodes[i].next=i+1<length?nodes+i+1:NULL;}
            ReverseNode *head=reverse_list(length?nodes:NULL),*node=head;
            for(size_t i=0;i<length;++i) {CHECK(node==nodes+length-1-i);CHECK(node->value==(int)((pattern>>(length-1-i))&1u));node=node->next;}
            CHECK(node==NULL);
            head=reverse_list(head); CHECK(head==(length?nodes:NULL));
            for(size_t i=0;i<length;++i) CHECK(nodes[i].next==(i+1<length?nodes+i+1:NULL));
            ++reverse_cases;
        }
    }
}

static void check_arena(void) {
    for(size_t capacity=0;capacity<=17;++capacity) {
        int cells[17],expected[17];bool allocated[17]={false};int *head=NULL;
        CHECK(arena_init(capacity?cells:NULL,capacity,&head));
        uint32_t random_state=123u+(uint32_t)capacity;
        for(unsigned step=0;step<2000;++step) {
            random_state=random_state*UINT32_C(1664525)+UINT32_C(1013904223);
            size_t live_slots=0;for(size_t i=0;i<capacity;++i) live_slots+=allocated[i];
            if(((random_state>>16)&1u)==0 || live_slots==0) {
                int *slot=arena_alloc(cells,&head);
                CHECK((slot==NULL)==(live_slots==capacity));
                if(slot) {
                    ptrdiff_t index=slot-cells;CHECK(index>=0 && (size_t)index<capacity && !allocated[index]);
                    allocated[index]=true;expected[index]=step%3==0?INT_MIN:step%3==1?INT_MAX:-1;
                    *slot=expected[index];
                }
            } else {
                size_t ordinal=(random_state>>1)%live_slots,index=0;
                while(!allocated[index] || ordinal--!=0) ++index;
                arena_free(cells,&head,cells+index);allocated[index]=false;
            }
            bool seen[17]={false};int *cursor=head;size_t free_count=0;
            while(cursor) {
                ptrdiff_t index=cursor-cells;CHECK(index>=0 && (size_t)index<capacity && !allocated[index] && !seen[index]);
                seen[index]=true;++free_count;int next=*cursor;
                CHECK(next==-1 || (next>=0 && (size_t)next<capacity));cursor=next==-1?NULL:cells+next;
            }
            size_t now_live=0;
            for(size_t i=0;i<capacity;++i) {now_live+=allocated[i];if(allocated[i]) CHECK(cells[i]==expected[i]);}
            CHECK(free_count+now_live==capacity);++arena_steps;
        }
    }
    int cell=7,*head=&cell;
    CHECK(!arena_init(&cell,(size_t)INT_MAX+1,&head) && cell==7 && head==&cell);
}

int main(void) {
    check_dictionary();check_reversal();check_arena();
    printf("{\"passed\":true,\"dictionary_histories\":%lu,\"reversal_cases\":%lu,\"arena_steps\":%lu,\"assertions\":%lu,\"live_blocks\":%zu}\n",
           dictionary_cases,reverse_cases,arena_steps,assertions,live_count);
    return 0;
}
