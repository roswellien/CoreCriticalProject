// Authored guest-memory contracts exercising the production source adapter.
struct TemporalSourceFixture : CaptureFixture {
    struct Register { unsigned dword{}; };
    struct { struct { Register rbp, rbx, rsi, rsp, rcx; } gpr; } state;
    struct { Renderer *sren{}; } host;
    struct WorldScope {
        unsigned node{}, mesh{};
        std::shared_ptr<const mw34::world::SourceBytes> source_bytes;
    };
    struct D3DCmd {
        std::shared_ptr<ModelInstance> model;
        std::shared_ptr<const mw34::temporal::Snapshot> camera_view;
        std::shared_ptr<const mw34::temporal::StaticSource> temporal_source;
        unsigned fixture_node{}, fixture_polygon{}, texture{};
    };
    struct Surface { unsigned guest{}; std::uint64_t version{}; };
    Surface *vsurface(unsigned) { return nullptr; }
    mw34::world::SnapshotCache<WorldScope> world_meshes{2048,64*1024*1024};
    std::shared_ptr<WorldScope> world_scope;
    std::uint64_t camera_flip_serial{};
    std::vector<std::pair<unsigned,unsigned>> allocations;
    void allocate(unsigned address,unsigned bytes) {
        allocations.emplace_back(address,bytes);
        for(unsigned i=0;i<bytes;i+=4)words[address+i]=0;
    }
    bool readable(unsigned address,unsigned bytes) const {
        return std::any_of(allocations.begin(),allocations.end(),[&](auto block){
            return address>=block.first && std::uint64_t(address)+bytes<=std::uint64_t(block.first)+block.second;
        });
    }
    void get_bytes(unsigned address,void *output,unsigned bytes) {
        auto *out=static_cast<unsigned char*>(output);
        for(unsigned i=0;i<bytes;++i)out[i]=static_cast<unsigned char>(load((address+i)&~3U)>>((address+i)%4*8));
    }
    unsigned override_parent(unsigned node) {
        return load(node+0x54)==1?load(load(node+0x58)):0;
    }
    static OverrideMatrix override_inverse(const OverrideMatrix &matrix) {
        mw34::temporal::Matrix input{};
        for(unsigned i=0;i<12;++i)input[i]=float(matrix[i]);
        const auto inverse=mw34::temporal::inverse_affine(input);
        auto result=identity();for(unsigned i=0;i<12;++i)result[i]=inverse[i];return result;
    }
    static void camera_advance(std::uint64_t &epoch) { ++epoch; }
    #include "temporal_source_stage.inc"
    static constexpr unsigned owner=0x10000,data=0x11000,frame=0x12080,cell=0x13000,
        chunks=0x14000,objects=0x15000,root=0x16000,root_data=0x17000,
        leaf=0x18000,leaf_data=0x19000,parents=0x1a000,children=0x1b000,record=0x1c000;
    TemporalSourceFixture() {
        for(unsigned address:{owner,data,frame-0x80,cell,chunks,objects,root,root_data,
                              leaf,leaf_data,parents,children,record})allocate(address,0x100);
        allocate(0x5ea534,4);allocate(0x736640,0x2d4);allocate(0x73fbb0,12);
        words[owner+0x38]=data;words[data+0x90]=chunks;words[chunks]=cell;
        words[frame-0xc]=data;words[frame-0x38]=cell;words[0x736910]=1;
        words[cell+0x38]=1U<<16;words[cell+0x3c]=objects;words[objects]=root;
        words[root+0x34]=words[leaf+0x34]=5;
        words[root+0x38]=root_data;words[leaf+0x38]=leaf_data;
        words[root_data]=words[leaf_data]=8;
        words[root+0x5c]=1;words[root+0x60]=children;words[children]=leaf;
        words[leaf+0x54]=1;words[leaf+0x58]=parents;words[parents]=root;
        state.gpr.rbp.dword=frame;
        temporal_cell_scope={owner,data,frame,0};
        temporal_source_load();
        auto scope=std::make_shared<WorldScope>();scope->node=leaf;scope->mesh=0x20000;
        world_meshes.put(scope->mesh,{1,2,3},scope);scope->source_bytes=world_meshes.source(scope->mesh);
        world_scope=scope;
        sun_view_binding.valid=true;
        sun_view_binding.renderer={};
        for(unsigned i:{0U,4U,8U})sun_view_binding.renderer[i]=std::bit_cast<unsigned>(1.f);
    }
    D3DCmd command() {
        D3DCmd draw{};draw.model=std::make_shared<ModelInstance>();draw.model->world=true;
        auto geometry=std::make_shared<ModelGeometry>();geometry->vertices={{0,0,2,0,0,1,0,0}};
        draw.model->geometry=geometry;draw.model->camera={1,0,0,0,0,1,0,0,0,0,1,0};
        draw.model->projection={1,20,20,32,32,.1f};draw.fixture_node=leaf;draw.fixture_polygon=0x21000;
        auto camera=std::make_shared<mw34::temporal::Snapshot>();
        camera->load_epoch=mw34::campaign::CampaignManager::instance().reader_epoch();draw.camera_view=camera;
        return draw;
    }
    void select() { temporal_placement=temporal_cell_record(0x4f69dc,root); }
};

static void temporal_source_checks() {
    require(mw34::temporal::enabled(),"Source fixture requires temporal inputs");
    TemporalSourceFixture f;f.select();require(bool(f.temporal_placement),"Valid cell-owned subtree rejected");
    auto first=f.command();f.temporal_source_capture(first);
    require(first.temporal_source&&!first.temporal_source->previous_static,"First source inherited history");
    ++f.camera_flip_serial;f.select();auto second=f.command();f.temporal_source_capture(second);
    require(second.temporal_source&&second.temporal_source->previous_static,"Unchanged source lost history");
    require(f.temporal_tracked_nodes.contains(f.parents)&&f.temporal_tracked_nodes.contains(f.children),
            "Ownership-list allocations escaped tracked lifetime");
    const auto parent_epoch=f.temporal_source_epoch;f.temporal_source_freed(f.parents,0x100);
    require(parent_epoch!=f.temporal_source_epoch,"Freed parent-list allocation retained admission");
    ++f.camera_flip_serial;f.select();auto parent_reused=f.command();f.temporal_source_capture(parent_reused);
    require(parent_reused.temporal_source&&!parent_reused.temporal_source->previous_static,
            "Reused parent-list bytes inherited source history");
    f.words[f.children]=0;auto stale=f.command();f.temporal_source_capture(stale);
    require(!stale.temporal_source,"Stale nonreciprocal parent inherited admission");f.words[f.children]=f.leaf;
    f.words[f.objects]=0;f.select();require(!f.temporal_placement,"Deleted cell membership was accepted");
    f.words[f.objects]=f.root;
    ++f.camera_flip_serial;f.words[0x73fbb0]=std::bit_cast<unsigned>(1.f);f.select();
    auto tile=f.command();f.temporal_source_capture(tile);
    require(tile.temporal_source&&!tile.temporal_source->previous_static,"Changed tile inherited history");
    const auto epoch=f.temporal_source_epoch;
    f.temporal_source_freed(f.leaf_data,0x100);
    require(f.temporal_source_epoch!=epoch,"Freed descendant pose storage retained source lifetime");
    auto freed=f.command();f.temporal_source_capture(freed);
    require(!freed.temporal_source,"Stale placement survived tracked storage release");
    ++f.camera_flip_serial;f.select();auto reused=f.command();f.temporal_source_capture(reused);
    require(reused.temporal_source&&!reused.temporal_source->previous_static,"Reused addresses inherited source history");
    require(first.temporal_source->epoch!=reused.temporal_source->epoch,"Deferred source lost its immutable epoch");
    f.words[f.root_data]=0;f.words[f.cell+0x40]=1;f.words[f.cell+0x44]=f.record;
    f.words[f.record]=f.root;f.state.gpr.rbx.dword=f.record;
    for(unsigned i=0;i<12;++i){const unsigned value=std::bit_cast<unsigned>(i==0||i==4||i==8?1.f:0.f);
        f.words[f.record+4+i*4]=f.words[f.root_data+0x30+i*4]=f.words[f.root_data+0x60+i*4]=value;}
    require(bool(f.temporal_cell_record(0x4f6ae0,f.root)),"Authentic placement matrix copies rejected");
    f.words[f.root_data+0x60]^=1;
    require(!f.temporal_cell_record(0x4f6ae0,f.root),"Changed original matrix copy was accepted");
    const auto before_load=f.temporal_source_epoch;
    mw34::campaign::CampaignManager::instance().observe_file("zbd/t1/readerm.zbd");f.temporal_source_load();
    require(f.temporal_source_epoch!=before_load&&f.temporal_node_bytes.empty()&&f.world_meshes.size()==0,
            "Reader load epoch retained old source lookup ownership");
    std::cout<<"Temporal sources: cell ownership, tile, matrix producer, deletion, freed/reused storage and load epochs pass\n";
}
