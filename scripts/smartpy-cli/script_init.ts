interface StorageSpec {
    value: TNat;
}

@Contract
export class Minimal {
    storage: StorageSpec = {
        value: 1,
    };

    @EntryPoint
    ep(value: TNat): void {
        this.storage.value = value;
    }
}

compileContract('minimal', new Minimal());
