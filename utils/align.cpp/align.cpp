#include <fstream>
#include <string>
#include <iostream>
#include <vector>
#include <utility>
#include <algorithm>
using namespace std;

// some useful macros
#define MIN2(x,y) ((x) <= (y) ? (x) : (y))
#define MIN3(x,y,z) ((x) <= (y) && (x) <= (z) ? (x) : MIN2(y,z))
#define MAX2(x,y) ((x) >= (y) ? (x) : (y))
#define MAX3(x,y,z) ((x) >= (y) && (x) >= (z) ? (x) : MAX2(y,z))
#define MAX4(w,x,y,z) MAX2(MAX3(w, x, y), z)


template<typename T> 
class ScoringMatrix {
    public:
    virtual int score(T one, T two) = 0;
    virtual bool is_mismatch(T one, T two) = 0;
};

template<typename T> 
class IdentityScoringMatrix: public ScoringMatrix<T> {
    private:
        int match, mismatch;

    public:
    IdentityScoringMatrix(int match=1, int mismatch=-1) {
        this->match = match;
        this->mismatch = mismatch;
    };

    bool is_mismatch(T one, T two) {
        return one != two;
    }

    int score(T one, T two) {   
        if (one == two) 
            return match;
        return mismatch;
    }
};

typedef IdentityScoringMatrix<string> WordScoringMatrix;


enum E_OPER : short {
OP_EMPTY, OP_INSERT, OP_DELETE, OP_MATCH, OP_MISMATCH, OP_DELIM
};

struct Alignment {
    int r_pos;
    int q_pos;
    int score;
    bool global;
    vector<pair<int, char> > cigar;
};

class AlignmentMatrix {

    private:
        short* cell_val;
        E_OPER* op;
        short* run;
        size_t _rows;
        size_t _cols;

    public:
        AlignmentMatrix(size_t rows, size_t cols) {
            cell_val = new short[rows * cols];
            op = new E_OPER[rows * cols];
            run = new short[rows * cols];
            _cols = cols;
            _rows = rows;
            init();
        };

        void init() {
            size_t x = 0;
            for (int i=0;i<_cols;i++) {
                for (int j=0;j<_rows;j++) {
                    x = j * _cols + i;
                    if (i==0 && j>0) {
                        op[x] = OP_INSERT;
                    } else if (j==0 && i>0) {
                        op[x] = OP_DELETE;
                    } else {
                        op[x] = OP_EMPTY;
                    }
                    run[x] = 0;
                    cell_val[x] = 0;
                }
            }
        }

        void set(size_t row, size_t col, short val, E_OPER oper, short r) {
            cell_val[row*_cols + col] = val;
            op[row*_cols + col] = oper;
            run[row*_cols + col] = r;
        }

        E_OPER get_op(size_t row, size_t col) {
            return op[row*_cols + col];
        }
        
        short get_val(size_t row, size_t col) { 
            return cell_val[row*_cols + col];
        }

        short get_run(size_t row, size_t col) { 
            return run[row*_cols + col];
        }

        ~AlignmentMatrix() {
            delete[] cell_val;
            delete[] op;
            delete[] run;
        };
};

template<typename T> 
class LocalAlignment {

    protected:

    vector<pair<int, char> > reduce_cigar(vector<E_OPER> operations) {
        int count = 1;
        E_OPER last = OP_EMPTY;
        vector<pair<int, char> > ret;
        char ops[] = {'\0','I','D','M','X'};
        for (auto op = operations.begin(); op != operations.end(); ++op) {
            if (last != OP_EMPTY && *op == last) {
                count ++;
            } else if (last != OP_EMPTY) {
                ret.push_back(pair<int, char>(count, ops[last]));
                count = 1;
            }
            last = *op;
        }

        if (last != OP_EMPTY) {
            ret.push_back(pair<int, char>(count, ops[last]));
        }
        return ret;
    }

    vector<pair<int, char> > cigar(vector<E_OPER> operations) {
        vector<pair<int, char> > ret;
        char ops[] = {'\0','I','D','M','X','Y'};
        for (auto op = operations.begin(); op != operations.end(); ++op) {
                ret.push_back(pair<int, char>(1, ops[*op]));
        }
        return ret;
    }

    
    public:

    ScoringMatrix<T>* _scoring_matrix;
    T _delim;
    short _gap_penalty;
    short _gap_extension_penalty;
    short _gap_extension_decay;
    bool _verbose;
    bool _prefer_gap_runs;
    bool _globalalign;
    bool _full_query;

    LocalAlignment(ScoringMatrix<T>* scoring_matrix, T delim, short gap_penalty=-1, short gap_extension_penalty=-1, short gap_extension_decay=0.0, bool prefer_gap_runs=true, bool verbose=false, bool globalalign=false, bool full_query=false) {
        _scoring_matrix = scoring_matrix;
        _gap_penalty = gap_penalty;
        _gap_extension_penalty = gap_extension_penalty;
        _gap_extension_decay = gap_extension_decay;
        _verbose = verbose;
        _prefer_gap_runs = prefer_gap_runs;
        _globalalign = globalalign;
        _full_query = full_query;
        _delim = delim;
    };

    Alignment align(vector<T> ref, vector<T> query) {
        int rows = query.size() + 1;
        int cols = ref.size() + 1;

        AlignmentMatrix matrix(rows, cols);

        short max_val = 0;
        int max_row = 0;
        int max_col = 0;

        short ins_val = 0;
        short del_val = 0;
        short c_val = 0;
        short mm_val;

        int row, col;

        // calculate matrix
        for (row = 1; row < rows; row++) {
            for (col = 1; col < cols; col++) {

                mm_val = matrix.get_val(row - 1, col - 1) + _scoring_matrix->score(query[row - 1], ref[col - 1]);

                short ins_run = 0;
                short del_run = 0;

                if (matrix.get_op(row - 1, col) == OP_INSERT) {
                    ins_run = matrix.get_run(row - 1, col);
                    if (matrix.get_val(row - 1, col) == 0 && ! _full_query) {
                        // no penalty to start the alignment
                        ins_val = 0;
                    } else {
                        if (!_gap_extension_decay ) {
                            ins_val = matrix.get_val(row - 1, col) + _gap_extension_penalty;
                        } else {
                            ins_val = matrix.get_val(row - 1, col) + MIN2(0, _gap_extension_penalty + ins_run * _gap_extension_decay);
                        }
                    }
                } else {
                    ins_val = matrix.get_val(row - 1, col) + _gap_penalty;
                }

                if (matrix.get_op(row, col - 1) == OP_DELETE) {
                    del_run = matrix.get_run(row, col - 1);
                    if (matrix.get_val(row, col - 1) == 0 && ! _full_query) {
                        // no penalty to start the alignment
                        del_val = 0;
                    } else {
                        if (! _gap_extension_decay) {
                            del_val = matrix.get_val(row, col - 1) + _gap_extension_penalty;
                        } else {
                            del_val = matrix.get_val(row, col - 1) + MIN2(0, _gap_extension_penalty + del_run * _gap_extension_decay);
                        }
                    }

                } else {
                    del_val = matrix.get_val(row, col - 1) + _gap_penalty;
                }

                if (query[row-1] == _delim) {
                    c_val = ins_val;
                    del_val = ins_val - 1;
                    mm_val = ins_val - 1;
                } else if (_globalalign or _full_query) {
                    c_val = MAX3(mm_val, del_val, ins_val);
                } else {
                    c_val = MAX4(mm_val, del_val, ins_val, 0);
                }

                if (! _prefer_gap_runs) {
                    ins_run = 0;
                    del_run = 0;
                }

                if (c_val >= max_val) {
                    max_val = c_val;
                    max_row = row;
                    max_col = col;
                }

                if (del_run && c_val == del_val) {
                    matrix.set(row, col, c_val, OP_DELETE, del_run + 1);
                } else if (ins_run && c_val == ins_val) {
                    matrix.set(row, col, c_val, OP_INSERT, ins_run + 1);
                } else if (c_val == mm_val) {
                    matrix.set(row, col, c_val, OP_MATCH, 0);
                } else if (c_val == del_val) {
                    matrix.set(row, col, c_val, OP_DELETE, 1);
                } else if (c_val == ins_val) {
                    matrix.set(row, col, c_val, OP_INSERT, 1);
                } else {
                    matrix.set(row, col, 0, OP_MISMATCH, 0);
                }                
            }
        }

        // backtrack
        if (_globalalign) {
            // backtrack from last cell
            row = rows - 1;
            col = cols - 1;
        } else if (_full_query) {
            // backtrack from max in last row
            row = rows - 1;
            max_val = 0;
            col = 0;
            for (int c=1; c < cols; c++) {
                if (matrix.get_val(row, c) > max_val) {
                    col = c;
                    max_val = matrix.get_val(row, c);
                }
            }
            col = cols - 1;
        } else {
            // backtrack from max
            row = max_row;
            col = max_col;
        }

        E_OPER oper = OP_EMPTY;
        vector<E_OPER> aln;
        while(true) {
            c_val = matrix.get_val(row, col);
            oper = matrix.get_op(row, col);
            if (oper == OP_INSERT && query[row-1] == _delim) {
                oper = OP_DELIM;
            }
            if (oper == OP_MATCH && _scoring_matrix->is_mismatch(ref[col-1],query[row-1])) {
                oper = OP_MISMATCH;
            }

            if (_globalalign) {
                if (row == 0 && col == 0) {
                    break;
                }
            } else if (_full_query) {
                if (row == 0) {
                    break;
                }
            } else {
                if (c_val <= 0) {
                    break;
                }
            }

            aln.push_back(oper);

            if (oper == OP_MATCH || oper == OP_MISMATCH) {
                row -= 1;
                col -= 1;
            } else if (oper == OP_INSERT || oper == OP_DELIM) {
                row -= 1;
            } else if (oper == OP_DELETE) {
                col -= 1;
            } else {
                break;
            }
        }

        reverse(aln.begin(), aln.end());

        Alignment ali;
        ali.q_pos = row;
        ali.r_pos = col;
        ali.score = max_val;
        ali.global = _globalalign;
        ali.cigar = cigar(aln);
        return ali;
    }
};

typedef LocalAlignment<string> WordLocalAlignment;


vector<string> read_file(char* name) {
    ifstream fin(name);
    string s;
    vector<string> result;
    while( fin >> s ) {
            result.push_back(s);
    }
    return result;
}

int main (int argc, char* argv[]) {
    if (argc < 3) {
        cout << "Usage: align asr ref" << endl;
        return 1;
    }

    // read files to vectors
    vector<string> asr = read_file(argv[1]);
    vector<string> ref = read_file(argv[2]);
    WordLocalAlignment sw(new WordScoringMatrix(1,-1), "|");
    sw._full_query = true;
    if (argc == 4) {
        if (argv[3][0] == 'f') {
            sw._full_query = false;
        }
        if (argv[3][1] == 't') {
            sw._globalalign  = true;
        }
        if (argv[3][2] == 'f') {
            sw._prefer_gap_runs  = false;
        }
    }

    Alignment ali = sw.align(ref, asr);

    cout << ali.r_pos << "\n";
    cout << ali.q_pos << "\n";
    for (auto op = ali.cigar.begin(); op != ali.cigar.end() ; ++op) {
        cout << (*op).first << (*op).second;
    }
    cout << "\n" << ali.score;
    cout << endl;
}

